# api/consulta_metabase.py
"""
Módulo principal para consultas ao Metabase
"""

from typing import Dict, List, Optional, Union
import json
from .metabase_client import metabase_client
from .filtros_captura import FiltrosCaptura
from .filtros_normalizacao import FiltrosNormalizacao
from .config import MAX_ROWS_WITHOUT_WARNING

class ConsultaMetabase:
    """Classe principal para executar consultas no Metabase"""
    
    def __init__(self):
        self.client = metabase_client
        self.filtros_captura = FiltrosCaptura()
        self.filtros_normalizacao = FiltrosNormalizacao()
    
    def executar_consulta(
        self,
        question_id: int,
        filtros: Optional[Dict[str, Union[str, List[str]]]] = None,
        formato: str = 'json'
    ) -> Union[List[Dict], Dict]:
        """
        Executa uma consulta no Metabase
        
        Args:
            question_id: ID da questão no Metabase
            filtros: Filtros a aplicar (opcional)
            formato: Formato de resposta (json, csv, etc.)
            
        Returns:
            Dados da consulta no formato especificado
        """
        # Se não foram passados filtros, tenta capturar da requisição atual
        if filtros is None:
            filtros = self.filtros_captura.capturar_parametros_request()
        
        # Normaliza os filtros
        filtros_normalizados = self.filtros_normalizacao.normalizar_filtros(filtros)
        
        # Log de debug
        self._log_consulta(question_id, filtros_normalizados)
        
        # Formata para o Metabase
        parametros_metabase = self.filtros_captura.formatar_para_metabase(filtros_normalizados)
        
        # Executa a consulta
        try:
            resultado = self.client.execute_question(question_id, parametros_metabase)
            
            # Aviso se muitos dados
            if isinstance(resultado, list) and len(resultado) > MAX_ROWS_WITHOUT_WARNING:
                print(f"\n⚠️ AVISO: {len(resultado):,} linhas retornadas. "
                      f"Considere aplicar mais filtros para melhor performance.")
            
            # Retorna no formato solicitado
            if formato == 'json':
                return resultado
            else:
                # Futura implementação de outros formatos
                return resultado
                
        except Exception as e:
            print(f"\n❌ Erro ao executar consulta: {str(e)}")
            return {
                'error': str(e),
                'question_id': question_id,
                'filtros': filtros_normalizados
            }
    
    def executar_consulta_com_processamento(
        self,
        question_id: int,
        filtros: Optional[Dict] = None,
        processamento: Optional[str] = None
    ) -> Union[List[Dict], Dict]:
        """
        Executa consulta e aplica processamento opcional
        
        Args:
            question_id: ID da questão
            filtros: Filtros a aplicar
            processamento: Tipo de processamento ('agregacao', 'transformacao', etc.)
            
        Returns:
            Dados processados
        """
        # Executa a consulta base
        dados = self.executar_consulta(question_id, filtros)
        
        if isinstance(dados, dict) and 'error' in dados:
            return dados
        
        # Aplica processamento se solicitado
        if processamento:
            # Importa o módulo de processamento adequado
            if processamento == 'agregacao':
                from .processamentoDados_agregacao import ProcessadorAgregacao
                processador = ProcessadorAgregacao()
                dados = processador.processar(dados)
            elif processamento == 'transformacao':
                from .processamentoDados_transformacao import ProcessadorTransformacao
                processador = ProcessadorTransformacao()
                dados = processador.processar(dados)
        
        return dados
    
    def obter_info_questao(self, question_id: int) -> Dict:
        """
        Obtém informações sobre uma questão
        
        Args:
            question_id: ID da questão
            
        Returns:
            Informações da questão
        """
        return self.client.get_question_info(question_id)
    
    def _log_consulta(self, question_id: int, filtros: Dict):
        """Log interno de consultas"""
        print(f"\n🔍 Executando consulta:")
        print(f"   Question ID: {question_id}")
        print(f"   Filtros ativos: {len(filtros)}")
        
        if filtros:
            print("   Filtros:")
            for key, value in filtros.items():
                if isinstance(value, list):
                    print(f"     • {key}: {len(value)} valores")
                else:
                    print(f"     • {key}: {value}")

# Instância global
consulta_metabase = ConsultaMetabase()
