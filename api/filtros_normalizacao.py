# api/filtros_normalizacao.py
"""
Módulo para normalização de parâmetros e filtros
"""

import urllib.parse
from typing import Dict, Union, List

class FiltrosNormalizacao:
    """Classe para normalizar nomes e valores de parâmetros"""
    
    # Mapa de normalização de nomes
    NORMALIZACAO_NOMES = {
        'posição': 'posicao',
        'posicao': 'posicao',
        'anúncio': 'anuncio',
        'anuncio': 'anuncio',
        'conversões_consideradas': 'conversoes_consideradas',
        'conversoes_consideradas': 'conversoes_consideradas',
        'objetivo': 'objective',
        'objective': 'objective'
    }
    
    # Mapa de normalização de valores (futuro)
    NORMALIZACAO_VALORES = {
        # Exemplo: 'LINK_CLICKS': 'link_clicks'
    }
    
    @staticmethod
    def normalizar_nome_parametro(nome: str) -> str:
        """
        Normaliza o nome de um parâmetro
        
        Args:
            nome: Nome do parâmetro
            
        Returns:
            Nome normalizado
        """
        # Tenta decodificar se ainda estiver codificado
        try:
            decoded_name = urllib.parse.unquote(nome)
            if decoded_name != nome:
                nome = decoded_name
        except:
            pass
        
        # Retorna o nome normalizado ou o original
        return FiltrosNormalizacao.NORMALIZACAO_NOMES.get(nome, nome)
    
    @staticmethod
    def normalizar_valor_parametro(valor: str, tipo_parametro: str = None) -> str:
        """
        Normaliza o valor de um parâmetro
        
        Args:
            valor: Valor do parâmetro
            tipo_parametro: Tipo do parâmetro (opcional)
            
        Returns:
            Valor normalizado
        """
        # Decodifica caracteres especiais
        try:
            # Substitui + por espaço (padrão URL)
            valor = valor.replace('+', ' ')
            # Decodifica outros caracteres
            valor = urllib.parse.unquote(valor)
        except:
            pass
        
        # Aplica normalização específica se houver
        if tipo_parametro and tipo_parametro in FiltrosNormalizacao.NORMALIZACAO_VALORES:
            mapa_valores = FiltrosNormalizacao.NORMALIZACAO_VALORES[tipo_parametro]
            if isinstance(mapa_valores, dict) and valor in mapa_valores:
                valor = mapa_valores[valor]
        
        return valor
    
    @staticmethod
    def normalizar_filtros(filtros: Dict[str, Union[str, List[str]]]) -> Dict[str, Union[str, List[str]]]:
        """
        Normaliza um dicionário completo de filtros
        
        Args:
            filtros: Dict com filtros originais
            
        Returns:
            Dict com filtros normalizados
        """
        filtros_normalizados = {}
        
        for nome, valor in filtros.items():
            # Normaliza o nome
            nome_normalizado = FiltrosNormalizacao.normalizar_nome_parametro(nome)
            
            # Normaliza o valor
            if isinstance(valor, list):
                # Lista de valores
                valores_normalizados = [
                    FiltrosNormalizacao.normalizar_valor_parametro(v, nome_normalizado)
                    for v in valor
                ]
                filtros_normalizados[nome_normalizado] = valores_normalizados
            else:
                # Valor único
                valor_normalizado = FiltrosNormalizacao.normalizar_valor_parametro(
                    valor, nome_normalizado
                )
                filtros_normalizados[nome_normalizado] = valor_normalizado
        
        return filtros_normalizados
    
    @staticmethod
    def validar_caracteres_especiais(valor: str) -> Dict[str, any]:
        """
        Valida e identifica caracteres especiais em um valor
        
        Args:
            valor: Valor a ser validado
            
        Returns:
            Dict com informações sobre caracteres especiais
        """
        caracteres_especiais = ['+', '&', '%', '=', '?', '#', '|', '/', '*', '@', 
                               '!', '$', '^', '(', ')', '[', ']', '{', '}']
        
        encontrados = [c for c in caracteres_especiais if c in valor]
        
        return {
            'valor_original': valor,
            'tem_especiais': len(encontrados) > 0,
            'caracteres': encontrados,
            'quantidade': len(encontrados)
        }
    
    @staticmethod
    def adicionar_nova_normalizacao(tipo: str, de: str, para: str):
        """
        Adiciona uma nova regra de normalização (para uso futuro)
        
        Args:
            tipo: 'nome' ou 'valor'
            de: Valor original
            para: Valor normalizado
        """
        if tipo == 'nome':
            FiltrosNormalizacao.NORMALIZACAO_NOMES[de] = para
        elif tipo == 'valor':
            # Implementar quando necessário
            pass
