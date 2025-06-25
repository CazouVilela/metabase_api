# api/processamentoDados_json.py
"""
Módulo para processamento e preparação de dados JSON
"""

from typing import List, Dict, Any, Optional, Union
import json
from datetime import datetime

class ProcessadorJSON:
    """Classe para processar e preparar dados JSON"""
    
    @staticmethod
    def preparar_para_tabela_virtual(
        dados: List[Dict],
        colunas: Optional[List[str]] = None,
        limite: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Prepara dados para renderização em tabela virtual
        
        Args:
            dados: Lista de dicionários com os dados
            colunas: Lista de colunas a incluir (None = todas)
            limite: Limite de linhas (None = sem limite)
            
        Returns:
            Dict com dados preparados para tabela virtual
        """
        if not dados:
            return {
                'dados': [],
                'colunas': [],
                'total_linhas': 0,
                'metadata': {}
            }
        
        # Determina colunas
        if colunas is None:
            colunas = list(dados[0].keys())
        
        # Aplica limite se necessário
        dados_limitados = dados[:limite] if limite else dados
        
        # Prepara metadata
        metadata = {
            'total_original': len(dados),
            'total_processado': len(dados_limitados),
            'limite_aplicado': limite is not None,
            'timestamp': datetime.now().isoformat(),
            'colunas_info': ProcessadorJSON._analisar_colunas(dados[:100])  # Analisa amostra
        }
        
        return {
            'dados': dados_limitados,
            'colunas': colunas,
            'total_linhas': len(dados_limitados),
            'metadata': metadata
        }
    
    @staticmethod
    def otimizar_para_transmissao(dados: List[Dict]) -> Dict[str, Any]:
        """
        Otimiza dados para transmissão eficiente
        Converte para formato colunar para reduzir tamanho
        
        Args:
            dados: Lista de dicionários
            
        Returns:
            Dict com dados em formato colunar
        """
        if not dados:
            return {'formato': 'colunar', 'colunas': {}, 'total': 0}
        
        # Converte para formato colunar
        colunas = {}
        for coluna in dados[0].keys():
            colunas[coluna] = [linha.get(coluna) for linha in dados]
        
        return {
            'formato': 'colunar',
            'colunas': colunas,
            'total': len(dados),
            'nomes_colunas': list(dados[0].keys())
        }
    
    @staticmethod
    def paginar_dados(
        dados: List[Dict],
        pagina: int = 1,
        por_pagina: int = 1000
    ) -> Dict[str, Any]:
        """
        Pagina dados para carregamento progressivo
        
        Args:
            dados: Lista completa de dados
            pagina: Número da página (1-based)
            por_pagina: Itens por página
            
        Returns:
            Dict com dados paginados e informações
        """
        total = len(dados)
        total_paginas = (total + por_pagina - 1) // por_pagina
        
        inicio = (pagina - 1) * por_pagina
        fim = min(inicio + por_pagina, total)
        
        return {
            'dados': dados[inicio:fim],
            'paginacao': {
                'pagina_atual': pagina,
                'total_paginas': total_paginas,
                'por_pagina': por_pagina,
                'total_itens': total,
                'inicio': inicio + 1,
                'fim': fim,
                'tem_proxima': pagina < total_paginas,
                'tem_anterior': pagina > 1
            }
        }
    
    @staticmethod
    def filtrar_colunas_vazias(dados: List[Dict]) -> List[str]:
        """
        Identifica colunas que estão totalmente vazias
        
        Args:
            dados: Lista de dados
            
        Returns:
            Lista de nomes de colunas não vazias
        """
        if not dados:
            return []
        
        # Analisa amostra
        amostra = dados[:min(100, len(dados))]
        colunas = list(dados[0].keys())
        colunas_validas = []
        
        for coluna in colunas:
            # Verifica se algum valor não é vazio
            tem_valor = any(
                linha.get(coluna) not in (None, '', ' ', 'null', 'NULL')
                for linha in amostra
            )
            if tem_valor:
                colunas_validas.append(coluna)
        
        return colunas_validas
    
    @staticmethod
    def _analisar_colunas(amostra: List[Dict]) -> Dict[str, Dict]:
        """
        Analisa tipos e características das colunas
        
        Args:
            amostra: Amostra de dados
            
        Returns:
            Dict com informações sobre cada coluna
        """
        if not amostra:
            return {}
        
        info_colunas = {}
        
        for coluna in amostra[0].keys():
            valores = [linha.get(coluna) for linha in amostra if linha.get(coluna) is not None]
            
            if not valores:
                info_colunas[coluna] = {'tipo': 'vazio', 'valores_unicos': 0}
                continue
            
            # Detecta tipo
            tipos = set()
            for valor in valores[:10]:  # Amostra pequena
                if isinstance(valor, (int, float)):
                    tipos.add('numero')
                elif isinstance(valor, bool):
                    tipos.add('booleano')
                else:
                    tipos.add('texto')
            
            # Conta valores únicos (limitado para performance)
            valores_unicos = len(set(str(v) for v in valores[:100]))
            
            info_colunas[coluna] = {
                'tipo': list(tipos)[0] if len(tipos) == 1 else 'misto',
                'valores_unicos': valores_unicos,
                'tem_nulos': any(v is None for v in valores)
            }
        
        return info_colunas
