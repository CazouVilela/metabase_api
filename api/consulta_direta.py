# api/consulta_direta.py
"""
Módulo para executar consultas diretas ao PostgreSQL
usando queries extraídas do Metabase
"""

from typing import Dict, List, Union, Optional, Generator
import time
from .query_extractor import query_extractor
from .postgres_client import postgres_client
from .filtros_captura import FiltrosCaptura
from .filtros_normalizacao import FiltrosNormalizacao

class ConsultaDireta:
    """Executa consultas diretas ao PostgreSQL com queries do Metabase"""
    
    def __init__(self):
        self.extractor = query_extractor
        self.postgres = postgres_client
        self.filtros_captura = FiltrosCaptura()
        self.filtros_normalizacao = FiltrosNormalizacao()
        
        # Configurações
        self.chunk_size = 5000  # Tamanho do chunk para streaming
        self.use_streaming = True  # Se deve usar streaming por padrão
        self.schema_padrao = 'road'
    
    def executar_consulta_direta(
        self,
        question_id: int,
        filtros: Optional[Dict[str, Union[str, List[str]]]] = None,
        streaming: Optional[bool] = None
    ) -> Union[List[Dict], Generator[List[Dict], None, None]]:
        """
        Executa consulta diretamente no PostgreSQL
        
        Args:
            question_id: ID da questão no Metabase
            filtros: Filtros a aplicar (opcional)
            streaming: Se deve usar streaming (None = auto)
            
        Returns:
            Lista completa ou generator de chunks
        """
        start_time = time.time()
        
        try:
            # Testa conexão primeiro
            if not self.postgres.testar_conexao():
                raise Exception("Não foi possível conectar ao PostgreSQL. Verifique as configurações.")
            
            # Captura filtros se não foram passados
            if filtros is None:
                filtros = self.filtros_captura.capturar_parametros_request()
            
            # Normaliza filtros
            filtros_normalizados = self.filtros_normalizacao.normalizar_filtros(filtros)
            
            print(f"\n🚀 Iniciando consulta direta para pergunta {question_id}")
            print(f"   Filtros ativos: {len(filtros_normalizados)}")
            
            # Extrai query SQL do Metabase
            try:
                query_template, template_tags = self.extractor.extrair_query_sql(question_id)
            except Exception as e:
                raise Exception(f"Erro ao extrair query da pergunta {question_id}: {str(e)}")
            
            # Substitui template tags pelos filtros
            try:
                query_sql = self.extractor.substituir_template_tags(query_template, filtros_normalizados)
                
                # Limpa campos problemáticos (JSON, etc)
                query_sql = self.extractor.limpar_campos_problematicos(query_sql)
                
            except Exception as e:
                raise Exception(f"Erro ao processar filtros: {str(e)}")
            
            # Configura schema
            try:
                self.postgres.configurar_schema(self.schema_padrao)
            except Exception as e:
                raise Exception(f"Erro ao configurar schema '{self.schema_padrao}': {str(e)}")
            
            # Decide se usa streaming
            if streaming is None:
                # Auto-decide baseado no tamanho estimado
                streaming = self._deve_usar_streaming(query_sql)
            
            # Executa a query
            if streaming:
                print("🌊 Usando streaming de dados...")
                return self._executar_com_streaming(query_sql)
            else:
                print("📦 Carregando dados completos...")
                return self._executar_completo(query_sql)
                
        except Exception as e:
            print(f"\n❌ Erro na consulta direta: {str(e)}")
            import traceback
            traceback.print_exc()
            raise
    
    def _deve_usar_streaming(self, query: str) -> bool:
        """
        Decide se deve usar streaming baseado na estimativa de linhas
        
        Args:
            query: Query SQL
            
        Returns:
            True se deve usar streaming
        """
        try:
            # Conta resultados estimados
            total = self.postgres.contar_resultados(query)
            
            print(f"📊 Total estimado: {total:,} linhas")
            
            # Usa streaming para mais de 10k linhas
            return total > 10000
            
        except Exception as e:
            print(f"⚠️ Erro ao estimar tamanho, usando streaming: {str(e)}")
            return True
    
    def _executar_com_streaming(self, query: str) -> Generator[List[Dict], None, None]:
        """
        Executa query com streaming
        
        Args:
            query: Query SQL
            
        Yields:
            Chunks de dados
        """
        # Retorna generator do postgres_client
        yield from self.postgres.executar_query(query, chunk_size=self.chunk_size)
    
    def _executar_completo(self, query: str) -> List[Dict]:
        """
        Executa query e retorna dados completos
        
        Args:
            query: Query SQL
            
        Returns:
            Lista completa de dados
        """
        return self.postgres.executar_query_completa(query)
    
    def executar_consulta_direta_simples(
        self,
        question_id: int,
        filtros: Optional[Dict] = None
    ) -> List[Dict]:
        """
        Versão simplificada que sempre retorna lista completa
        (mantida para compatibilidade)
        
        Args:
            question_id: ID da questão
            filtros: Filtros a aplicar
            
        Returns:
            Lista completa de dados
        """
        # Força modo não-streaming
        resultado = self.executar_consulta_direta(question_id, filtros, streaming=False)
        
        # Se por algum motivo retornar generator, converte para lista
        if hasattr(resultado, '__iter__') and not isinstance(resultado, list):
            dados = []
            for chunk in resultado:
                dados.extend(chunk)
            return dados
        
        return resultado
    
    def testar_configuracao(self, database: str = None, schema: str = None) -> bool:
        """
        Testa a configuração de conexão
        
        Args:
            database: Nome do banco (opcional)
            schema: Nome do schema (opcional)
            
        Returns:
            True se conexão está OK
        """
        # Atualiza configurações se fornecidas
        if database:
            self.postgres.connection_params['database'] = database
        if schema:
            self.schema_padrao = schema
        
        # Testa conexão
        if not self.postgres.testar_conexao():
            return False
        
        # Configura schema
        try:
            self.postgres.configurar_schema(self.schema_padrao)
            print(f"✅ Configuração testada com sucesso!")
            print(f"   Database: {self.postgres.connection_params['database']}")
            print(f"   Schema: {self.schema_padrao}")
            return True
            
        except Exception as e:
            print(f"❌ Erro ao configurar schema: {str(e)}")
            return False
    
    def obter_estatisticas(self) -> Dict:
        """Retorna estatísticas da execução"""
        return {
            'chunk_size': self.chunk_size,
            'use_streaming': self.use_streaming,
            'schema': self.schema_padrao,
            'database': self.postgres.connection_params['database']
        }

# Instância global
consulta_direta = ConsultaDireta()
