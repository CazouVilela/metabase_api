# api/processamentoDados_transformacao.py
"""
Módulo para transformações de dados
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
import re

class ProcessadorTransformacao:
    """Classe para transformar dados de diferentes formas"""
    
    @staticmethod
    def normalizar_valores_monetarios(dados: List[Dict], campos_monetarios: List[str]) -> List[Dict]:
        """
        Normaliza valores monetários para formato consistente
        
        Args:
            dados: Lista de dados
            campos_monetarios: Lista de campos que contêm valores monetários
            
        Returns:
            Dados com valores normalizados
        """
        for linha in dados:
            for campo in campos_monetarios:
                if campo in linha and linha[campo] is not None:
                    # Converte para float e arredonda para 2 casas
                    try:
                        valor = float(linha[campo])
                        linha[campo] = round(valor, 2)
                    except (ValueError, TypeError):
                        linha[campo] = 0.0
        
        return dados
    
    @staticmethod
    def adicionar_campos_calculados(dados: List[Dict], calculos: Dict[str, str]) -> List[Dict]:
        """
        Adiciona campos calculados aos dados
        
        Args:
            dados: Lista de dados
            calculos: Dict com nome_campo: formula
            
        Returns:
            Dados com campos calculados adicionados
        """
        for linha in dados:
            for campo_novo, formula in calculos.items():
                try:
                    # Avalia a fórmula no contexto da linha
                    # ATENÇÃO: Em produção, use uma abordagem mais segura
                    resultado = eval(formula, {"__builtins__": {}}, linha)
                    linha[campo_novo] = resultado
                except Exception as e:
                    linha[campo_novo] = None
        
        return dados
    
    @staticmethod
    def converter_datas(dados: List[Dict], campos_data: List[str], formato_saida: str = "%d/%m/%Y") -> List[Dict]:
        """
        Converte campos de data para formato brasileiro
        
        Args:
            dados: Lista de dados
            campos_data: Lista de campos que contêm datas
            formato_saida: Formato de saída desejado
            
        Returns:
            Dados com datas formatadas
        """
        formatos_entrada = [
            "%Y-%m-%d",
            "%Y-%m-%d %H:%M:%S",
            "%d/%m/%Y",
            "%d-%m-%Y"
        ]
        
        for linha in dados:
            for campo in campos_data:
                if campo in linha and linha[campo]:
                    data_original = linha[campo]
                    
                    # Tenta converter com diferentes formatos
                    for formato in formatos_entrada:
                        try:
                            data_obj = datetime.strptime(str(data_original), formato)
                            linha[campo] = data_obj.strftime(formato_saida)
                            break
                        except ValueError:
                            continue
        
        return dados
    
    @staticmethod
    def limpar_strings(dados: List[Dict], campos_texto: Optional[List[str]] = None) -> List[Dict]:
        """
        Limpa e normaliza campos de texto
        
        Args:
            dados: Lista de dados
            campos_texto: Campos específicos (None = todos os campos string)
            
        Returns:
            Dados com strings limpas
        """
        for linha in dados:
            campos = campos_texto or linha.keys()
            
            for campo in campos:
                if campo in linha and isinstance(linha[campo], str):
                    # Remove espaços extras
                    texto = linha[campo].strip()
                    # Remove múltiplos espaços
                    texto = re.sub(r'\s+', ' ', texto)
                    # Remove caracteres de controle
                    texto = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', texto)
                    
                    linha[campo] = texto
        
        return dados
    
    @staticmethod
    def renomear_campos(dados: List[Dict], mapeamento: Dict[str, str]) -> List[Dict]:
        """
        Renomeia campos dos dados
        
        Args:
            dados: Lista de dados
            mapeamento: Dict com campo_original: campo_novo
            
        Returns:
            Dados com campos renomeados
        """
        dados_novos = []
        
        for linha in dados:
            nova_linha = {}
            for campo_original, valor in linha.items():
                campo_novo = mapeamento.get(campo_original, campo_original)
                nova_linha[campo_novo] = valor
            dados_novos.append(nova_linha)
        
        return dados_novos
    
    @staticmethod
    def filtrar_campos(dados: List[Dict], campos_manter: List[str]) -> List[Dict]:
        """
        Mantém apenas os campos especificados
        
        Args:
            dados: Lista de dados
            campos_manter: Lista de campos a manter
            
        Returns:
            Dados filtrados
        """
        dados_filtrados = []
        
        for linha in dados:
            nova_linha = {
                campo: linha.get(campo)
                for campo in campos_manter
                if campo in linha
            }
            dados_filtrados.append(nova_linha)
        
        return dados_filtrados
    
    @staticmethod
    def adicionar_ranking(dados: List[Dict], campo_ordenacao: str, nome_ranking: str = "ranking") -> List[Dict]:
        """
        Adiciona campo de ranking baseado em ordenação
        
        Args:
            dados: Lista de dados
            campo_ordenacao: Campo usado para ordenar
            nome_ranking: Nome do campo de ranking
            
        Returns:
            Dados com ranking adicionado
        """
        # Ordena os dados
        dados_ordenados = sorted(
            dados,
            key=lambda x: x.get(campo_ordenacao, 0),
            reverse=True
        )
        
        # Adiciona ranking
        for i, linha in enumerate(dados_ordenados, 1):
            linha[nome_ranking] = i
        
        return dados_ordenados
    
    @staticmethod
    def processar(dados: List[Dict], configuracao: Dict[str, Any]) -> List[Dict]:
        """
        Processa dados com base em configuração
        
        Args:
            dados: Lista de dados
            configuracao: Dict com transformações a aplicar
            
        Returns:
            Dados transformados
        """
        processador = ProcessadorTransformacao()
        
        # Aplica transformações conforme configuração
        if 'normalizar_monetarios' in configuracao:
            dados = processador.normalizar_valores_monetarios(
                dados, 
                configuracao['normalizar_monetarios']
            )
        
        if 'campos_calculados' in configuracao:
            dados = processador.adicionar_campos_calculados(
                dados,
                configuracao['campos_calculados']
            )
        
        if 'converter_datas' in configuracao:
            dados = processador.converter_datas(
                dados,
                configuracao['converter_datas']
            )
        
        if 'limpar_strings' in configuracao:
            dados = processador.limpar_strings(
                dados,
                configuracao.get('limpar_strings')
            )
        
        if 'renomear_campos' in configuracao:
            dados = processador.renomear_campos(
                dados,
                configuracao['renomear_campos']
            )
        
        if 'filtrar_campos' in configuracao:
            dados = processador.filtrar_campos(
                dados,
                configuracao['filtrar_campos']
            )
        
        if 'adicionar_ranking' in configuracao:
            dados = processador.adicionar_ranking(
                dados,
                configuracao['adicionar_ranking']
            )
        
        return dados
