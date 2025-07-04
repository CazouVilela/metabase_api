# api/query_extractor.py
"""
Módulo para extrair query SQL de perguntas do Metabase
"""

import re
from typing import Dict, List, Tuple, Optional
from .metabase_client import metabase_client

class QueryExtractor:
    """Extrai e processa queries SQL do Metabase"""
    
    def __init__(self):
        self.client = metabase_client
        self._query_cache = {}  # Cache de queries por question_id
    
    def extrair_query_sql(self, question_id: int) -> Tuple[str, List[str]]:
        """
        Extrai a query SQL nativa de uma pergunta do Metabase
        
        Args:
            question_id: ID da pergunta
            
        Returns:
            Tupla com (query_sql, lista_de_template_tags)
        """
        # Verifica cache
        if question_id in self._query_cache:
            print(f"📦 Query do cache para pergunta {question_id}")
            return self._query_cache[question_id]
        
        try:
            # Obtém informações da pergunta
            info = self.client.get_question_info(question_id)
            
            # Verifica se é uma query nativa
            if info.get('dataset_query', {}).get('type') != 'native':
                raise ValueError(f"Pergunta {question_id} não é uma query SQL nativa")
            
            # Extrai a query
            query_sql = info['dataset_query']['native']['query']
            
            # Extrai template tags
            template_tags = self._extrair_template_tags(query_sql)
            
            # Adiciona ao cache
            self._query_cache[question_id] = (query_sql, template_tags)
            
            print(f"✅ Query extraída: {len(query_sql)} caracteres, {len(template_tags)} tags")
            
            return query_sql, template_tags
            
        except Exception as e:
            print(f"❌ Erro ao extrair query: {str(e)}")
            raise
    
    def _extrair_template_tags(self, query: str) -> List[str]:
        """
        Extrai todos os template tags da query
        
        Args:
            query: Query SQL com template tags
            
        Returns:
            Lista de nomes dos template tags
        """
        # Padrão para encontrar {{tag}} no Metabase
        pattern = r'\{\{([^}]+)\}\}'
        matches = re.findall(pattern, query)
        
        # Remove duplicatas e limpa espaços
        tags = list(set(tag.strip() for tag in matches))
        
        print(f"📋 Template tags encontrados: {tags}")
        
        return tags
    
    def substituir_template_tags(
        self, 
        query: str, 
        filtros: Dict[str, any]
    ) -> str:
        """
        Substitui template tags pelos valores dos filtros
        
        Args:
            query: Query SQL com template tags
            filtros: Dict com valores dos filtros
            
        Returns:
            Query SQL com tags substituídos
        """
        query_processada = query
        
        # Log para debug
        print(f"\n🔧 Substituindo template tags:")
        print(f"   Filtros recebidos: {list(filtros.keys())}")
        
        # Processa cada filtro disponível
        for nome_filtro, valor in filtros.items():
            if not valor:  # Pula valores vazios
                continue
                
            # Padrão genérico para qualquer template tag
            # Constrói o padrão sem f-string para evitar problemas
            pattern = "[[AND {{" + nome_filtro + "}}]]"
            
            # Verifica se o padrão existe na query
            if pattern in query_processada:
                # Constrói a cláusula SQL
                sql_clause = self._construir_clausula_sql(nome_filtro, valor)
                
                if sql_clause:
                    replacement = f"AND {sql_clause}"
                    query_processada = query_processada.replace(pattern, replacement)
                    print(f"   ✅ Substituído: {nome_filtro} -> {sql_clause[:50]}...")
                else:
                    # Remove o padrão se não há valor
                    query_processada = query_processada.replace(pattern, "")
                    print(f"   ⚠️ Removido: {nome_filtro} (sem valor)")
            else:
                print(f"   ⚠️ Tag não encontrada na query: {nome_filtro}")
        
        # Remove quaisquer template tags restantes não utilizados
        import re
        
        # Primeiro remove tags dentro de [[AND {{...}}]]
        tags_restantes = re.findall(r'\[\[AND \{\{[^}]+\}\}\]\]', query_processada)
        if tags_restantes:
            print(f"   🔹 Removendo {len(tags_restantes)} tags não utilizadas")
            query_processada = re.sub(r'\[\[AND \{\{[^}]+\}\}\]\]', '', query_processada)
        
        # IMPORTANTE: Remove também tags soltas {{...}} que não estão dentro de [[AND ...]]
        # Isso resolve o problema do WHERE {{action_type_filter}}
        tags_soltas = re.findall(r'\{\{[^}]+\}\}', query_processada)
        if tags_soltas:
            print(f"   🔸 Removendo {len(tags_soltas)} tags soltas: {tags_soltas}")
            # Para action_type_filter especificamente, substitui WHERE {{action_type_filter}} por WHERE 1=1
            query_processada = re.sub(r'WHERE\s+\{\{action_type_filter\}\}', 'WHERE 1=1', query_processada, flags=re.IGNORECASE)
            # Remove outras tags soltas
            query_processada = re.sub(r'\{\{[^}]+\}\}', '', query_processada)
        
        # Remove espaços extras e linhas vazias
        query_processada = re.sub(r'\n\s*\n', '\n', query_processada)
        
        return query_processada
    
    def _construir_clausula_sql(self, campo: str, valor: any) -> str:
        """
        Constrói cláusula SQL para um filtro
        
        Args:
            campo: Nome do campo
            valor: Valor do filtro (string, lista ou dict)
            
        Returns:
            Cláusula SQL formatada
        """
        if not valor:
            return ""
        
        # Mapeamento de campos para colunas SQL
        campo_sql = self._mapear_campo_sql(campo)
        
        # Trata diferentes tipos de valores
        if isinstance(valor, list):
            # Múltiplos valores - usa IN
            valores_escapados = [self._escapar_valor_sql(v) for v in valor]
            valores_sql = ", ".join(f"'{v}'" for v in valores_escapados)
            return f"{campo_sql} IN ({valores_sql})"
            
        elif isinstance(valor, str) and "~" in valor:
            # Range de datas
            datas = valor.split("~")
            if len(datas) == 2:
                return f"{campo_sql} BETWEEN '{datas[0]}' AND '{datas[1]}'"
            
        else:
            # Valor único
            valor_escapado = self._escapar_valor_sql(valor)
            return f"{campo_sql} = '{valor_escapado}'"
    
    def _mapear_campo_sql(self, campo: str) -> str:
        """
        Mapeia nome do filtro para coluna SQL
        
        Args:
            campo: Nome do campo do filtro
            
        Returns:
            Nome da coluna SQL
        """
        mapeamento = {
            'data': 'date',
            'conta': 'account_name',
            'campanha': 'campaign_name',
            'adset': 'adset_name',
            'ad_name': 'ad_name',
            'plataforma': 'publisher_platform',
            'posicao': 'platform_position',
            'device': 'impression_device',
            'objective': 'objective',
            'optimization_goal': 'optimization_goal',
            'buying_type': 'buying_type',
            'action_type_filter': 'action_type'  # Especial - usado em subquery
        }
        
        return mapeamento.get(campo, campo)
    
    def _escapar_valor_sql(self, valor: str) -> str:
        """
        Escapa valor para prevenir SQL injection
        
        Args:
            valor: Valor a ser escapado
            
        Returns:
            Valor escapado
        """
        if not isinstance(valor, str):
            valor = str(valor)
        
        # Escapa aspas simples duplicando
        return valor.replace("'", "''")
    
    def limpar_campos_problematicos(self, query: str) -> str:
        """
        Remove ou ajusta campos que podem causar problemas na serialização
        
        Args:
            query: Query SQL
            
        Returns:
            Query ajustada
        """
        # Lista de campos problemáticos conhecidos
        campos_problematicos = {
            'conversions_json': 'conversions',  # Campo JSONB
            'conversions as conversions_json': "'' as conversions_json"  # Remove o alias problemático
        }
        
        query_limpa = query
        
        # Substitui campos problemáticos
        for campo_antigo, campo_novo in campos_problematicos.items():
            if campo_antigo in query_limpa:
                query_limpa = query_limpa.replace(campo_antigo, campo_novo)
                print(f"   🔧 Ajustado campo: {campo_antigo} -> {campo_novo}")
        
        return query_limpa
    
    def limpar_cache(self):
        """Limpa o cache de queries"""
        self._query_cache.clear()
        print("🗑️ Cache de queries limpo")

# Instância global
query_extractor = QueryExtractor()
