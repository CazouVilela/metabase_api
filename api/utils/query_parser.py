"""
Parser para queries SQL do Metabase
"""

import re
from typing import Dict, List, Any

class QueryParser:
    """Processa e transforma queries SQL"""
    
    # Mapeamento de campos para colunas SQL
    FIELD_MAPPING = {
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
        'action_type_filter': 'action_type'
    }
    
    # Campos problemáticos conhecidos
    PROBLEMATIC_FIELDS = {
        'conversions_json': 'conversions',
        'conversions as conversions_json': "'' as conversions_json"
    }
    
    def apply_filters(self, query: str, filters: Dict[str, Any]) -> str:
        """
        Substitui template tags pelos valores dos filtros
        """
        query_processed = query
        
        print(f"\n🔧 Substituindo template tags:")
        print(f"   Filtros recebidos: {list(filters.keys())}")
        
        # Processa cada filtro disponível
        for filter_name, value in filters.items():
            if not value:
                continue
                
            # Padrão genérico para qualquer template tag
            pattern = f"[[AND {{{{{filter_name}}}}}]]"
            
            # Verifica se o padrão existe na query
            if pattern in query_processed:
                # Constrói a cláusula SQL
                sql_clause = self._build_sql_clause(filter_name, value)
                
                if sql_clause:
                    replacement = f"AND {sql_clause}"
                    query_processed = query_processed.replace(pattern, replacement)
                    print(f"   ✅ Substituído: {filter_name} -> {sql_clause[:50]}...")
                else:
                    # Remove o padrão se não há valor
                    query_processed = query_processed.replace(pattern, "")
                    print(f"   ⚠️ Removido: {filter_name} (sem valor)")
            else:
                print(f"   ⚠️ Tag não encontrada na query: {filter_name}")
        
        # Remove template tags restantes
        query_processed = self._remove_unused_tags(query_processed)
        
        # Remove espaços extras e linhas vazias
        query_processed = re.sub(r'\n\s*\n', '\n', query_processed)
        
        return query_processed
    
    def _build_sql_clause(self, field: str, value: Any) -> str:
        """Constrói cláusula SQL para um filtro"""
        if not value:
            return ""
        
        # Mapeamento de campos para colunas SQL
        sql_field = self.FIELD_MAPPING.get(field, field)
        
        # Trata diferentes tipos de valores
        if isinstance(value, list):
            # Múltiplos valores - usa IN
            escaped_values = [self._escape_sql_value(v) for v in value]
            values_sql = ", ".join(f"'{v}'" for v in escaped_values)
            return f"{sql_field} IN ({values_sql})"
            
        elif isinstance(value, str) and "~" in value:
            # Range de datas
            dates = value.split("~")
            if len(dates) == 2:
                return f"{sql_field} BETWEEN '{dates[0]}' AND '{dates[1]}'"
            
        else:
            # Valor único
            escaped_value = self._escape_sql_value(value)
            return f"{sql_field} = '{escaped_value}'"
    
    def _escape_sql_value(self, value: str) -> str:
        """Escapa valor para prevenir SQL injection"""
        if not isinstance(value, str):
            value = str(value)
        
        # Escapa aspas simples duplicando
        return value.replace("'", "''")
    
    def _remove_unused_tags(self, query: str) -> str:
        """Remove template tags não utilizados"""
        # Remove tags dentro de [[AND {{...}}]]
        tags_restantes = re.findall(r'\[\[AND \{\{[^}]+\}\}\]\]', query)
        if tags_restantes:
            print(f"   🔹 Removendo {len(tags_restantes)} tags não utilizadas")
            query = re.sub(r'\[\[AND \{\{[^}]+\}\}\]\]', '', query)
        
        # Remove tags soltas {{...}}
        tags_soltas = re.findall(r'\{\{[^}]+\}\}', query)
        if tags_soltas:
            print(f"   🔸 Removendo {len(tags_soltas)} tags soltas: {tags_soltas}")
            # Para action_type_filter, substitui WHERE {{action_type_filter}} por WHERE 1=1
            query = re.sub(r'WHERE\s+\{\{action_type_filter\}\}', 'WHERE 1=1', query, flags=re.IGNORECASE)
            # Remove outras tags soltas
            query = re.sub(r'\{\{[^}]+\}\}', '', query)
        
        return query
    
    def clean_problematic_fields(self, query: str) -> str:
        """Remove ou ajusta campos que podem causar problemas na serialização"""
        query_clean = query
        
        # Substitui campos problemáticos
        for old_field, new_field in self.PROBLEMATIC_FIELDS.items():
            if old_field in query_clean:
                query_clean = query_clean.replace(old_field, new_field)
                print(f"   🔧 Ajustado campo: {old_field} -> {new_field}")
        
        return query_clean
    
    def extract_template_tags(self, query: str) -> List[str]:
        """Extrai todos os template tags da query"""
        # Padrão para encontrar {{tag}}
        pattern = r'\{\{([^}]+)\}\}'
        matches = re.findall(pattern, query)
        
        # Remove duplicatas e limpa espaços
        tags = list(set(tag.strip() for tag in matches))
        
        print(f"📋 Template tags encontrados: {tags}")
        
        return tags
