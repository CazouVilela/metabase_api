# api/processamentoDados_agregacao.py
"""
Módulo para agregações e cálculos estatísticos
"""

from typing import List, Dict, Any, Optional, Tuple
from collections import defaultdict
from datetime import datetime
import statistics

class ProcessadorAgregacao:
    """Classe para realizar agregações e cálculos em dados"""
    
    @staticmethod
    def agrupar_por(dados: List[Dict], campos_agrupamento: List[str]) -> Dict[Tuple, List[Dict]]:
        """
        Agrupa dados por um ou mais campos
        
        Args:
            dados: Lista de dados
            campos_agrupamento: Campos para agrupar
            
        Returns:
            Dict com chaves de agrupamento e listas de dados
        """
        grupos = defaultdict(list)
        
        for linha in dados:
            # Cria chave de agrupamento
            chave = tuple(linha.get(campo) for campo in campos_agrupamento)
            grupos[chave].append(linha)
        
        return dict(grupos)
    
    @staticmethod
    def calcular_metricas(
        dados: List[Dict], 
        metricas: Dict[str, Dict[str, str]]
    ) -> Dict[str, Any]:
        """
        Calcula métricas agregadas
        
        Args:
            dados: Lista de dados
            metricas: Dict com configuração das métricas
                     Ex: {'total_spend': {'campo': 'spend', 'operacao': 'soma'}}
            
        Returns:
            Dict com métricas calculadas
        """
        resultado = {}
        
        for nome_metrica, config in metricas.items():
            campo = config['campo']
            operacao = config['operacao']
            
            # Extrai valores não nulos
            valores = [
                float(linha.get(campo, 0)) 
                for linha in dados 
                if linha.get(campo) is not None
            ]
            
            if not valores:
                resultado[nome_metrica] = 0
                continue
            
            # Calcula métrica baseada na operação
            if operacao == 'soma':
                resultado[nome_metrica] = sum(valores)
            elif operacao == 'media':
                resultado[nome_metrica] = statistics.mean(valores)
            elif operacao == 'mediana':
                resultado[nome_metrica] = statistics.median(valores)
            elif operacao == 'minimo':
                resultado[nome_metrica] = min(valores)
            elif operacao == 'maximo':
                resultado[nome_metrica] = max(valores)
            elif operacao == 'contagem':
                resultado[nome_metrica] = len(valores)
            elif operacao == 'desvio_padrao':
                resultado[nome_metrica] = statistics.stdev(valores) if len(valores) > 1 else 0
            
        return resultado
    
    @staticmethod
    def criar_resumo_por_grupo(
        dados: List[Dict],
        campos_agrupamento: List[str],
        metricas: Dict[str, Dict[str, str]]
    ) -> List[Dict]:
        """
        Cria resumo agregado por grupos
        
        Args:
            dados: Lista de dados
            campos_agrupamento: Campos para agrupar
            metricas: Configuração das métricas
            
        Returns:
            Lista com resumos por grupo
        """
        # Agrupa dados
        grupos = ProcessadorAgregacao.agrupar_por(dados, campos_agrupamento)
        
        resumos = []
        
        for chave_grupo, dados_grupo in grupos.items():
            resumo = {}
            
            # Adiciona campos de agrupamento
            for i, campo in enumerate(campos_agrupamento):
                resumo[campo] = chave_grupo[i]
            
            # Calcula métricas para o grupo
            metricas_grupo = ProcessadorAgregacao.calcular_metricas(dados_grupo, metricas)
            resumo.update(metricas_grupo)
            
            # Adiciona contagem de registros
            resumo['quantidade_registros'] = len(dados_grupo)
            
            resumos.append(resumo)
        
        return resumos
    
    @staticmethod
    def calcular_percentuais(
        dados: List[Dict],
        campo_valor: str,
        campo_percentual: str = 'percentual'
    ) -> List[Dict]:
        """
        Adiciona campo de percentual relativo ao total
        
        Args:
            dados: Lista de dados
            campo_valor: Campo com valores para calcular percentual
            campo_percentual: Nome do campo de percentual
            
        Returns:
            Dados com percentuais adicionados
        """
        # Calcula total
        total = sum(
            float(linha.get(campo_valor, 0))
            for linha in dados
            if linha.get(campo_valor) is not None
        )
        
        if total == 0:
            return dados
        
        # Adiciona percentuais
        for linha in dados:
            valor = float(linha.get(campo_valor, 0))
            linha[campo_percentual] = round((valor / total) * 100, 2)
        
        return dados
    
    @staticmethod
    def calcular_variacao_temporal(
        dados: List[Dict],
        campo_data: str,
        campo_valor: str,
        periodo: str = 'mensal'
    ) -> List[Dict]:
        """
        Calcula variação temporal de valores
        
        Args:
            dados: Lista de dados
            campo_data: Campo com datas
            campo_valor: Campo com valores
            periodo: 'diario', 'semanal', 'mensal', 'anual'
            
        Returns:
            Lista com agregações temporais
        """
        # Agrupa por período
        agregacoes = defaultdict(lambda: {'soma': 0, 'contagem': 0})
        
        for linha in dados:
            if campo_data not in linha or campo_valor not in linha:
                continue
            
            try:
                # Parse da data
                data = linha[campo_data]
                if isinstance(data, str):
                    data = datetime.strptime(data, "%Y-%m-%d")
                
                # Define chave baseada no período
                if periodo == 'diario':
                    chave = data.strftime("%Y-%m-%d")
                elif periodo == 'semanal':
                    chave = f"{data.year}-S{data.isocalendar()[1]:02d}"
                elif periodo == 'mensal':
                    chave = data.strftime("%Y-%m")
                elif periodo == 'anual':
                    chave = str(data.year)
                else:
                    chave = data.strftime("%Y-%m-%d")
                
                # Agrega valores
                valor = float(linha[campo_valor])
                agregacoes[chave]['soma'] += valor
                agregacoes[chave]['contagem'] += 1
                
            except (ValueError, TypeError):
                continue
        
        # Converte para lista ordenada
        resultado = []
        for periodo_key in sorted(agregacoes.keys()):
            resultado.append({
                'periodo': periodo_key,
                'total': round(agregacoes[periodo_key]['soma'], 2),
                'quantidade': agregacoes[periodo_key]['contagem'],
                'media': round(
                    agregacoes[periodo_key]['soma'] / agregacoes[periodo_key]['contagem'], 
                    2
                )
            })
        
        return resultado
    
    @staticmethod
    def criar_tabela_cruzada(
        dados: List[Dict],
        campo_linha: str,
        campo_coluna: str,
        campo_valor: str,
        operacao: str = 'soma'
    ) -> Dict[str, Dict[str, Any]]:
        """
        Cria tabela cruzada (pivot table)
        
        Args:
            dados: Lista de dados
            campo_linha: Campo para linhas
            campo_coluna: Campo para colunas
            campo_valor: Campo com valores
            operacao: 'soma', 'media', 'contagem'
            
        Returns:
            Dict representando tabela cruzada
        """
        tabela = defaultdict(lambda: defaultdict(list))
        
        # Coleta valores
        for linha in dados:
            valor_linha = linha.get(campo_linha, 'Outros')
            valor_coluna = linha.get(campo_coluna, 'Outros')
            valor = linha.get(campo_valor, 0)
            
            if valor is not None:
                tabela[valor_linha][valor_coluna].append(float(valor))
        
        # Aplica operação
        resultado = {}
        for linha_key, colunas in tabela.items():
            resultado[linha_key] = {}
            
            for coluna_key, valores in colunas.items():
                if operacao == 'soma':
                    resultado[linha_key][coluna_key] = sum(valores)
                elif operacao == 'media':
                    resultado[linha_key][coluna_key] = statistics.mean(valores) if valores else 0
                elif operacao == 'contagem':
                    resultado[linha_key][coluna_key] = len(valores)
                else:
                    resultado[linha_key][coluna_key] = sum(valores)
        
        return resultado
    
    @staticmethod
    def processar(dados: List[Dict], tipo_agregacao: str = 'resumo', **kwargs) -> Any:
        """
        Processa agregação conforme tipo solicitado
        
        Args:
            dados: Lista de dados
            tipo_agregacao: Tipo de agregação ('resumo', 'temporal', 'pivot')
            **kwargs: Parâmetros específicos para cada tipo
            
        Returns:
            Resultado da agregação
        """
        processador = ProcessadorAgregacao()
        
        if tipo_agregacao == 'resumo':
            return processador.criar_resumo_por_grupo(
                dados,
                kwargs.get('campos_agrupamento', []),
                kwargs.get('metricas', {})
            )
        
        elif tipo_agregacao == 'temporal':
            return processador.calcular_variacao_temporal(
                dados,
                kwargs.get('campo_data', 'date'),
                kwargs.get('campo_valor', 'spend'),
                kwargs.get('periodo', 'mensal')
            )
        
        elif tipo_agregacao == 'pivot':
            return processador.criar_tabela_cruzada(
                dados,
                kwargs.get('campo_linha', 'campaign_name'),
                kwargs.get('campo_coluna', 'platform_position'),
                kwargs.get('campo_valor', 'spend'),
                kwargs.get('operacao', 'soma')
            )
        
        else:
            return dados
