# api/native_performance.py
"""
API com performance EXATA do Metabase nativo
Sem chunks, sem streaming - tudo otimizado como o Metabase faz
"""

import psycopg2
import psycopg2.extras
import json
import gzip
import time
from typing import Dict, List, Any, Tuple
from contextlib import contextmanager
from decimal import Decimal
from datetime import datetime, date
import redis
import hashlib
from flask import Response, request

class NativePerformanceAPI:
    """API que replica a performance do Metabase nativo"""
    
    def __init__(self):
        # Pool de conexões PERSISTENTE (como Metabase)
        self.connection_pool = []
        self.max_pool_size = 20
        self.prepared_statements = {}
        
        # Cache Redis (como Metabase usa)
        try:
            self.redis_client = redis.Redis(
                host='localhost',
                port=6379,
                decode_responses=False  # Vamos usar bytes para performance
            )
            self.cache_enabled = True
        except:
            self.cache_enabled = False
            print("⚠️ Redis não disponível, cache desabilitado")
        
        # TTL do cache (5 minutos como Metabase)
        self.cache_ttl = 300
        
        # Inicializa pool
        self._init_connection_pool()
    
    def _init_connection_pool(self):
        """Cria pool de conexões persistentes"""
        print("🔌 Inicializando pool de conexões...")
        
        for i in range(5):  # Começa com 5 conexões
            try:
                conn = psycopg2.connect(
                    host='localhost',
                    port=5432,
                    database='agencias',
                    user='cazouvilela',
                    password='$Riprip001',
                    # Otimizações de conexão
                    options='-c statement_timeout=600000 -c work_mem=256MB',
                    connect_timeout=5
                )
                # IMPORTANTE: Usar cursor padrão, não RealDictCursor
                conn.set_session(autocommit=True)
                self.connection_pool.append(conn)
            except Exception as e:
                print(f"⚠️ Erro ao criar conexão {i}: {e}")
    
    @contextmanager
    def get_connection(self):
        """Pega conexão do pool (sem criar nova!)"""
        conn = None
        try:
            # Tenta pegar do pool
            while self.connection_pool and not conn:
                candidate = self.connection_pool.pop()
                try:
                    # Testa se ainda está viva
                    candidate.isolation_level
                    conn = candidate
                except:
                    # Conexão morta, descarta
                    pass
            
            # Se não tem no pool, cria nova
            if not conn:
                conn = psycopg2.connect(
                    host='localhost',
                    port=5432,
                    database='agencias',
                    user='cazouvilela',
                    password='$Riprip001',
                    options='-c statement_timeout=600000 -c work_mem=256MB'
                )
                conn.set_session(autocommit=True)
            
            yield conn
            
            # Retorna ao pool
            if len(self.connection_pool) < self.max_pool_size:
                self.connection_pool.append(conn)
                conn = None
                
        finally:
            if conn:
                conn.close()
    
    def executar_query_nativa(self, question_id: int, query_sql: str, cache_key: str) -> Tuple[List, List, float]:
        """
        Executa query EXATAMENTE como Metabase nativo
        Retorna: (colunas, linhas, tempo_execucao)
        """
        start_time = time.time()
        
        # 1. Verifica cache primeiro
        if self.cache_enabled:
            cached = self._get_from_cache(cache_key)
            if cached:
                print("📦 Cache hit! Retornando instantaneamente")
                return cached['cols'], cached['rows'], 0.001
        
        # 2. Executa query com cursor PADRÃO (não dict)
        with self.get_connection() as conn:
            with conn.cursor() as cursor:
                # Configura para melhor performance
                cursor.execute("SET work_mem = '256MB'")
                cursor.execute("SET random_page_cost = 1.1")
                
                print(f"🚀 Executando query nativa (sem chunks!)...")
                cursor.execute(query_sql)
                
                # Pega metadata das colunas
                cols = [
                    {
                        'name': desc[0],
                        'base_type': self._get_pg_type(desc[1]),
                        'display_name': desc[0].replace('_', ' ').title()
                    }
                    for desc in cursor.description
                ]
                
                # Pega TODOS os dados de uma vez (como Metabase!)
                rows = cursor.fetchall()
                
                execution_time = time.time() - start_time
                print(f"✅ {len(rows):,} linhas em {execution_time:.2f}s")
                
                # 3. Processa dados para formato otimizado
                processed_rows = self._process_rows_native(rows)
                
                # 4. Salva no cache
                if self.cache_enabled and len(rows) > 0:
                    self._save_to_cache(cache_key, {
                        'cols': cols,
                        'rows': processed_rows,
                        'row_count': len(rows),
                        'cached_at': time.time()
                    })
                
                return cols, processed_rows, execution_time
    
    def _process_rows_native(self, rows: List[tuple]) -> List[List]:
        """
        Processa linhas para formato nativo do Metabase
        Converte tuplas em listas, serializa tipos especiais
        """
        processed = []
        
        for row in rows:
            processed_row = []
            for value in row:
                if isinstance(value, Decimal):
                    processed_row.append(float(value))
                elif isinstance(value, (datetime, date)):
                    processed_row.append(value.isoformat())
                elif isinstance(value, dict):
                    # JSONB fields - mantém como dict
                    processed_row.append(value)
                elif value is None:
                    processed_row.append(None)
                else:
                    processed_row.append(value)
            processed.append(processed_row)
        
        return processed
    
    def _get_pg_type(self, type_code: int) -> str:
        """Mapeia tipo PostgreSQL para tipo Metabase"""
        type_map = {
            16: 'type/Boolean',
            20: 'type/BigInteger',
            21: 'type/Integer',
            23: 'type/Integer',
            25: 'type/Text',
            114: 'type/JSON',
            700: 'type/Float',
            701: 'type/Float',
            1082: 'type/Date',
            1114: 'type/DateTime',
            1184: 'type/DateTimeWithTZ',
            1700: 'type/Decimal',
            3802: 'type/JSON'  # JSONB
        }
        return type_map.get(type_code, 'type/Text')
    
    def _get_from_cache(self, key: str) -> Dict:
        """Pega do cache Redis"""
        try:
            data = self.redis_client.get(f"metabase:query:{key}")
            if data:
                # Descomprime e deserializa
                return json.loads(gzip.decompress(data).decode('utf-8'))
        except Exception as e:
            print(f"⚠️ Erro ao ler cache: {e}")
        return None
    
    def _save_to_cache(self, key: str, data: Dict):
        """Salva no cache Redis comprimido"""
        try:
            # Serializa e comprime
            json_data = json.dumps(data, separators=(',', ':'))
            compressed = gzip.compress(json_data.encode('utf-8'))
            
            # Salva com TTL
            self.redis_client.setex(
                f"metabase:query:{key}",
                self.cache_ttl,
                compressed
            )
            
            print(f"💾 Cache salvo: {len(json_data)} → {len(compressed)} bytes "
                  f"({100 - len(compressed)/len(json_data)*100:.1f}% compressão)")
        except Exception as e:
            print(f"⚠️ Erro ao salvar cache: {e}")
    
    def gerar_cache_key(self, question_id: int, filtros: Dict) -> str:
        """Gera chave de cache única"""
        # Ordena filtros para consistência
        filtros_ordenados = json.dumps(filtros, sort_keys=True)
        key_string = f"{question_id}:{filtros_ordenados}"
        return hashlib.sha256(key_string.encode()).hexdigest()[:16]
    
    def criar_response_nativa(self, cols: List, rows: List, metadata: Dict) -> Response:
        """
        Cria response EXATAMENTE como Metabase
        Com compressão gzip e formato otimizado
        """
        # Formato nativo do Metabase
        response_data = {
            'data': {
                'cols': cols,
                'rows': rows,
                'rows_truncated': len(rows),
                'results_metadata': {
                    'columns': cols
                }
            },
            'database_id': 2,
            'started_at': metadata.get('started_at'),
            'json_query': {},
            'average_execution_time': metadata.get('execution_time', 0) * 1000,  # em ms
            'status': 'completed',
            'context': 'question',
            'row_count': len(rows),
            'running_time': int(metadata.get('execution_time', 0) * 1000)
        }
        
        # Serializa para JSON compacto
        json_data = json.dumps(response_data, separators=(',', ':'))
        
        # Comprime com gzip
        compressed = gzip.compress(json_data.encode('utf-8'))
        
        print(f"📦 Response: {len(json_data)} → {len(compressed)} bytes "
              f"({100 - len(compressed)/len(json_data)*100:.1f}% compressão)")
        
        # Retorna com headers corretos
        response = Response(compressed)
        response.headers['Content-Type'] = 'application/json'
        response.headers['Content-Encoding'] = 'gzip'
        response.headers['X-Metabase-Client'] = 'native-performance'
        
        return response

# Instância global
native_api = NativePerformanceAPI()

# Função para integrar com Flask
def executar_query_performance_nativa(question_id: int, filtros: Dict):
    """Executa query com performance nativa do Metabase"""
    from api.query_extractor import query_extractor
    
    # Extrai e processa query
    query_template, _ = query_extractor.extrair_query_sql(question_id)
    query_sql = query_extractor.substituir_template_tags(query_template, filtros)
    query_sql = query_extractor.limpar_campos_problematicos(query_sql)
    
    # Gera cache key
    cache_key = native_api.gerar_cache_key(question_id, filtros)
    
    # Executa com API nativa
    started_at = time.time()
    cols, rows, execution_time = native_api.executar_query_nativa(
        question_id, 
        query_sql, 
        cache_key
    )
    
    # Cria response nativa
    metadata = {
        'started_at': started_at,
        'execution_time': execution_time
    }
    
    return native_api.criar_response_nativa(cols, rows, metadata)
