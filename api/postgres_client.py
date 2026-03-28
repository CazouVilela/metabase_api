# api/postgres_client.py
"""
Cliente para conexão direta ao PostgreSQL
"""

import os
import psycopg2
import psycopg2.extras
from typing import List, Dict, Any, Optional, Generator
from contextlib import contextmanager
import time
from dotenv import load_dotenv
load_dotenv('/home/cazouvilela/credenciais/database/postgres_main.env')
import json
from decimal import Decimal

class PostgresClient:
    """Cliente para executar queries diretamente no PostgreSQL"""
    
    def __init__(self):
        self.connection_params = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'port': int(os.getenv('DB_PORT', '15432')),
            'database': os.getenv('DB_NAME', 'agencias'),
            'user': os.getenv('DB_USER', 'cazouvilela'),
            'password': os.getenv('POSTGRES_PASSWORD', '')
        }
        self._connection_pool = []
        self.max_pool_size = 5
        
    @contextmanager
    def get_connection(self):
        """Context manager para obter conexão do pool"""
        conn = None
        try:
            # Tenta obter do pool
            if self._connection_pool:
                conn = self._connection_pool.pop()
                # Verifica se conexão ainda está viva
                try:
                    conn.isolation_level
                except:
                    conn = None
            
            # Cria nova conexão se necessário
            if not conn:
                conn = psycopg2.connect(**self.connection_params)
                # Configura para retornar dicts
                conn.cursor_factory = psycopg2.extras.RealDictCursor
                
                # Registra adaptadores para tipos especiais
                self._registrar_adaptadores(conn)
            
            yield conn
            
            # Retorna ao pool se não estiver cheio
            if len(self._connection_pool) < self.max_pool_size:
                self._connection_pool.append(conn)
                conn = None
                
        finally:
            # Fecha conexão se não foi para o pool
            if conn:
                conn.close()
    
    def _registrar_adaptadores(self, conn):
        """Registra adaptadores para tipos PostgreSQL especiais"""
        # Registra handler para JSON/JSONB
        psycopg2.extras.register_default_json(loads=json.loads)
        psycopg2.extras.register_default_jsonb(loads=json.loads)
    
    def _serializar_valor(self, valor: Any) -> Any:
        """Serializa valores especiais para JSON"""
        if isinstance(valor, Decimal):
            return float(valor)
        elif isinstance(valor, (dict, list)):
            # Se já é dict/list (vindo de JSON/JSONB), retorna como está
            return valor
        elif hasattr(valor, '__dict__'):
            # Objeto complexo - tenta converter
            return str(valor)
        else:
            return valor
    
    def _processar_linha(self, linha: Dict) -> Dict:
        """Processa uma linha para garantir que seja serializável"""
        linha_processada = {}
        
        for chave, valor in linha.items():
            try:
                # Tenta serializar o valor
                linha_processada[chave] = self._serializar_valor(valor)
            except Exception as e:
                # Se falhar, converte para string
                print(f"⚠️ Aviso: Erro ao serializar campo '{chave}': {str(e)}")
                linha_processada[chave] = str(valor) if valor is not None else None
        
        return linha_processada
    
    def executar_query(
        self, 
        query: str, 
        params: Optional[tuple] = None,
        chunk_size: int = 5000
    ) -> Generator[List[Dict], None, None]:
        """
        Executa query com cursor server-side para performance
        
        Args:
            query: Query SQL
            params: Parâmetros da query (opcional)
            chunk_size: Tamanho do chunk para streaming
            
        Yields:
            Chunks de resultados
        """
        start_time = time.time()
        total_rows = 0
        
        with self.get_connection() as conn:
            # Usa server-side cursor para grandes datasets
            with conn.cursor(name='metabase_cursor') as cursor:
                # Define o tamanho do fetch
                cursor.itersize = chunk_size
                
                print(f"\n🔍 Executando query direta no PostgreSQL...")
                print(f"   Chunk size: {chunk_size:,} linhas")
                
                try:
                    # Executa a query
                    cursor.execute(query, params)
                    
                    # Processa em chunks
                    chunk_num = 0
                    while True:
                        chunk = cursor.fetchmany(chunk_size)
                        if not chunk:
                            break
                        
                        chunk_num += 1
                        total_rows += len(chunk)
                        
                        # Converte para lista de dicts com processamento
                        rows = [self._processar_linha(dict(row)) for row in chunk]
                        
                        elapsed = time.time() - start_time
                        print(f"   📦 Chunk {chunk_num}: {len(rows):,} linhas "
                              f"(Total: {total_rows:,} em {elapsed:.1f}s)")
                        
                        yield rows
                        
                except psycopg2.ProgrammingError as e:
                    print(f"\n❌ Erro SQL: {str(e)}")
                    print(f"\n📄 Query problemática (primeiros 500 chars):")
                    print(query[:500])
                    raise
                except Exception as e:
                    print(f"\n❌ Erro na execução: {type(e).__name__}: {str(e)}")
                    raise
        
        elapsed = time.time() - start_time
        print(f"\n✅ Query completa: {total_rows:,} linhas em {elapsed:.1f}s")
        print(f"   Velocidade: {total_rows/elapsed:.0f} linhas/segundo")
    
    def executar_query_completa(
        self, 
        query: str, 
        params: Optional[tuple] = None
    ) -> List[Dict]:
        """
        Executa query e retorna todos os resultados de uma vez
        (usar apenas para queries pequenas)
        
        Args:
            query: Query SQL
            params: Parâmetros da query
            
        Returns:
            Lista completa de resultados
        """
        start_time = time.time()
        
        with self.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, params)
                results = cursor.fetchall()
                
                # Converte para lista de dicts com processamento
                rows = [self._processar_linha(dict(row)) for row in results]
        
        elapsed = time.time() - start_time
        print(f"✅ Query executada: {len(rows):,} linhas em {elapsed:.2f}s")
        
        return rows
    
    def contar_resultados(self, query: str, params: Optional[tuple] = None) -> int:
        """
        Conta o número de resultados de uma query
        
        Args:
            query: Query SQL
            params: Parâmetros da query
            
        Returns:
            Número de linhas
        """
        # Modifica query para COUNT
        count_query = f"SELECT COUNT(*) as total FROM ({query}) as subquery"
        
        with self.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(count_query, params)
                result = cursor.fetchone()
                return result['total']
    
    def testar_conexao(self) -> bool:
        """Testa se a conexão está funcionando"""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT 1")
                    result = cursor.fetchone()
                    return result is not None
        except Exception as e:
            print(f"❌ Erro ao testar conexão: {str(e)}")
            return False
    
    def configurar_schema(self, schema: str = 'road'):
        """
        Configura o schema padrão para as queries
        
        Args:
            schema: Nome do schema
        """
        with self.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(f"SET search_path TO {schema}, public")
                conn.commit()
        
        print(f"✅ Schema configurado: {schema}")
    
    def fechar_pool(self):
        """Fecha todas as conexões do pool"""
        while self._connection_pool:
            conn = self._connection_pool.pop()
            conn.close()
        
        print("🔌 Pool de conexões fechado")

# Instância global
postgres_client = PostgresClient()
