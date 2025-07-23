"""
Serviço principal de execução de queries
Concentra toda a lógica de Native Performance
"""

import psycopg2
import psycopg2.extras
import json
import gzip
import time
import hashlib
from typing import Dict, List, Any, Tuple
from contextlib import contextmanager
from decimal import Decimal
from datetime import datetime, date
from flask import Response

from config.settings import DATABASE_CONFIG, PERFORMANCE_CONFIG, DB_SCHEMA
from api.services.metabase_service import MetabaseService
from api.services.cache_service import CacheService
from api.utils.query_parser import QueryParser

class QueryService:
    """Serviço de execução de queries com performance nativa"""
    
    def __init__(self):
        self.metabase_service = MetabaseService()
        self.cache_service = CacheService()
        self.query_parser = QueryParser()
        
        # Pool de conexões PERSISTENTE
        self.connection_pool = []
        self.max_pool_size = PERFORMANCE_CONFIG['max_pool_size']
        self.prepared_statements = {}
        
        # Inicializa pool
        self._init_connection_pool()
    
    def _init_connection_pool(self):
        """Cria pool de conexões persistentes"""
        print("🔌 Inicializando pool de conexões...")
        
        for i in range(5):  # Começa com 5 conexões
            try:
                conn = psycopg2.connect(**DATABASE_CONFIG)
                conn.set_session(autocommit=True)
                self.connection_pool.append(conn)
            except Exception as e:
                print(f"⚠️ Erro ao criar conexão {i}: {e}")
    
    @contextmanager
    def get_connection(self):
        """Pega conexão do pool"""
        conn = None
        try:
            # Tenta pegar do pool
            while self.connection_pool and not conn:
                candidate = self.connection_pool.pop()
                try:
                    candidate.isolation_level
                    conn = candidate
                except:
                    pass
            
            # Se não tem no pool, cria nova
            if not conn:
                conn = psycopg2.connect(**DATABASE_CONFIG)
                conn.set_session(autocommit=True)
            
            yield conn
            
            # Retorna ao pool
            if len(self.connection_pool) < self.max_pool_size:
                self.connection_pool.append(conn)
                conn = None
                
        finally:
            if conn:
                conn.close()
    
    def execute_query(self, question_id: int, filters: Dict) -> Response:
        """
        Executa query e retorna Response no formato do Metabase
        """

	# DEBUG: Log detalhado dos filtros
	print("\n" + "="*60)
    	print("🔍 DEBUG - Filtros recebidos:")
    	for key, value in filters.items():
       	    print(f"   {key}: {value} (tipo: {type(value).__name__})")
    	print("="*60 + "\n")

        # Gera cache key
        cache_key = self._generate_cache_key(question_id, filters)
        
        # Verifica cache
        cached = self.cache_service.get(cache_key)
        if cached:
            print("📦 Cache hit! Retornando instantaneamente")
            return self._create_response(cached['cols'], cached['rows'], {
                'started_at': time.time(),
                'execution_time': 0.001,
                'from_cache': True
            })
        
        # Extrai e processa query
        query_info = self.metabase_service.get_question_query(question_id)
        query_sql = self.query_parser.apply_filters(query_info['query'], filters)
        query_sql = self.query_parser.clean_problematic_fields(query_sql)
        
        # Executa query
        started_at = time.time()
        cols, rows, execution_time = self._execute_native_query(query_sql)
        
        # Salva no cache se houver dados
        if self.cache_service.enabled and len(rows) > 0:
            self.cache_service.set(cache_key, {
                'cols': cols,
                'rows': rows,
                'row_count': len(rows),
                'cached_at': time.time()
            })
        
        # Cria response
        return self._create_response(cols, rows, {
            'started_at': started_at,
            'execution_time': execution_time,
            'from_cache': False
        })
    
    def _execute_native_query(self, query_sql: str) -> Tuple[List, List, float]:
        """Executa query com cursor padrão para máxima performance"""
        start_time = time.time()
        
        with self.get_connection() as conn:
            with conn.cursor() as cursor:

                # Configura para melhor performance
                cursor.execute(f"SET search_path TO {DB_SCHEMA}, public")
                cursor.execute("SET work_mem = '256MB'")
                cursor.execute("SET random_page_cost = 1.1")
                
                print(f"🚀 Executando query nativa...")
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
                
                # Pega TODOS os dados de uma vez
                rows = cursor.fetchall()
                
                execution_time = time.time() - start_time
                print(f"✅ {len(rows):,} linhas em {execution_time:.2f}s")
                
                # Processa dados para formato otimizado
                processed_rows = self._process_rows_native(rows)
                
                return cols, processed_rows, execution_time
    
    def _process_rows_native(self, rows: List[tuple]) -> List[List]:
        """Processa linhas para formato nativo do Metabase"""
        processed = []
        
        for row in rows:
            processed_row = []
            for value in row:
                if isinstance(value, Decimal):
                    processed_row.append(float(value))
                elif isinstance(value, (datetime, date)):
                    processed_row.append(value.isoformat())
                elif isinstance(value, dict):
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
            3802: 'type/JSON'
        }
        return type_map.get(type_code, 'type/Text')
    
    def _generate_cache_key(self, question_id: int, filters: Dict) -> str:
        """Gera chave de cache única"""
        filters_ordenados = json.dumps(filters, sort_keys=True)
        key_string = f"{question_id}:{filters_ordenados}"
        return hashlib.sha256(key_string.encode()).hexdigest()[:16]
    
    def _create_response(self, cols: List, rows: List, metadata: Dict) -> Response:
        """Cria response no formato exato do Metabase"""
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
            'average_execution_time': metadata.get('execution_time', 0) * 1000,
            'status': 'completed',
            'context': 'question',
            'row_count': len(rows),
            'running_time': int(metadata.get('execution_time', 0) * 1000),
            'from_cache': metadata.get('from_cache', False)
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
    
    def get_question_info(self, question_id: int) -> Dict:
        """Obtém informações sobre uma questão"""
        return self.metabase_service.get_question_info(question_id)
    
    def close_pool(self):
        """Fecha todas as conexões do pool"""
        while self.connection_pool:
            conn = self.connection_pool.pop()
            conn.close()
        print("🔌 Pool de conexões fechado")
