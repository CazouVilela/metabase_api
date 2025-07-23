"""
Parser para queries SQL do Metabase
"""

import re
from typing import Dict, List, Any
from datetime import datetime, timedelta

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
    
    # Mapeamento COMPLETO de filtros de data relativos do Metabase
    RELATIVE_DATE_FILTERS = {
        # Dias específicos
        'today': lambda: (datetime.now().date(), datetime.now().date()),
        'yesterday': lambda: ((datetime.now() - timedelta(days=1)).date(), (datetime.now() - timedelta(days=1)).date()),
        
        # Últimos X dias (incluindo hoje)
        'past7days': lambda: ((datetime.now() - timedelta(days=6)).date(), datetime.now().date()),
        'past30days': lambda: ((datetime.now() - timedelta(days=29)).date(), datetime.now().date()),
        'past60days': lambda: ((datetime.now() - timedelta(days=59)).date(), datetime.now().date()),
        'past90days': lambda: ((datetime.now() - timedelta(days=89)).date(), datetime.now().date()),
        'past12months': lambda: ((datetime.now() - timedelta(days=364)).date(), datetime.now().date()),
        'past13months': lambda: ((datetime.now() - timedelta(days=394)).date(), datetime.now().date()),
        'past15months': lambda: ((datetime.now() - timedelta(days=455)).date(), datetime.now().date()),
        'past2years': lambda: ((datetime.now() - timedelta(days=729)).date(), datetime.now().date()),
        
        # Próximos X dias
        'next7days': lambda: (datetime.now().date(), (datetime.now() + timedelta(days=6)).date()),
        'next30days': lambda: (datetime.now().date(), (datetime.now() + timedelta(days=29)).date()),
        'next60days': lambda: (datetime.now().date(), (datetime.now() + timedelta(days=59)).date()),
        'next90days': lambda: (datetime.now().date(), (datetime.now() + timedelta(days=89)).date()),
        'next12months': lambda: (datetime.now().date(), (datetime.now() + timedelta(days=364)).date()),
        
        # Semanas
        'thisweek': lambda: QueryParser._get_current_week(),
        'lastweek': lambda: QueryParser._get_last_week(),
        'last2weeks': lambda: ((datetime.now() - timedelta(days=13)).date(), datetime.now().date()),
        'last3weeks': lambda: ((datetime.now() - timedelta(days=20)).date(), datetime.now().date()),
        'last4weeks': lambda: ((datetime.now() - timedelta(days=27)).date(), datetime.now().date()),
        'last12weeks': lambda: ((datetime.now() - timedelta(days=83)).date(), datetime.now().date()),
        
        # Meses
        'thismonth': lambda: QueryParser._get_current_month(),
        'lastmonth': lambda: QueryParser._get_last_month(),
        'last3months': lambda: ((datetime.now() - timedelta(days=89)).date(), datetime.now().date()),
        'last6months': lambda: ((datetime.now() - timedelta(days=179)).date(), datetime.now().date()),
        'last12months': lambda: ((datetime.now() - timedelta(days=364)).date(), datetime.now().date()),
        
        # Trimestres
        'thisquarter': lambda: QueryParser._get_current_quarter(),
        'lastquarter': lambda: QueryParser._get_last_quarter(),
        
        # Anos
        'thisyear': lambda: QueryParser._get_current_year(),
        'lastyear': lambda: QueryParser._get_last_year(),
        
        # Especiais
        'alltime': lambda: (datetime(2000, 1, 1).date(), datetime.now().date()),
        
        # Aliases comuns
        'last7days': lambda: ((datetime.now() - timedelta(days=6)).date(), datetime.now().date()),
        'last30days': lambda: ((datetime.now() - timedelta(days=29)).date(), datetime.now().date()),
        'last60days': lambda: ((datetime.now() - timedelta(days=59)).date(), datetime.now().date()),
        'last90days': lambda: ((datetime.now() - timedelta(days=89)).date(), datetime.now().date()),
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
        
        # Tratamento especial para filtros de data
        if field == 'data':
            return self._build_date_clause(sql_field, value)
        
        # Trata diferentes tipos de valores
        if isinstance(value, list):
            # Múltiplos valores - usa IN
            escaped_values = [self._escape_sql_value(v) for v in value]
            values_sql = ", ".join(f"'{v}'" for v in escaped_values)
            return f"{sql_field} IN ({values_sql})"
            
        else:
            # Valor único
            escaped_value = self._escape_sql_value(value)
            return f"{sql_field} = '{escaped_value}'"
    
    def _build_date_clause(self, sql_field: str, value: str) -> str:
        """Constrói cláusula SQL para filtros de data"""
        
        # Se valor é None ou vazio, retorna vazio
        if not value:
            return ""
        
        # Converte para string se necessário
        value = str(value)
        
        # Remove espaços extras
        value = value.strip()
        
        # Verifica se é um filtro relativo (case insensitive)
        if value.lower() in self.RELATIVE_DATE_FILTERS:
            print(f"   📅 Convertendo filtro relativo: {value}")
            start_date, end_date = self.RELATIVE_DATE_FILTERS[value.lower()]()
            
            if start_date == end_date:
                return f"{sql_field} = '{start_date}'"
            else:
                return f"{sql_field} BETWEEN '{start_date}' AND '{end_date}'"
        
        # Verifica se é um range (formato: data1~data2)
        elif "~" in value:
            dates = value.split("~")
            if len(dates) == 2:
                # Limpa espaços das datas
                date1 = dates[0].strip()
                date2 = dates[1].strip()
                
                # Se alguma data estiver vazia, ignora
                if date1 and date2:
                    return f"{sql_field} BETWEEN '{date1}' AND '{date2}'"
                elif date1:
                    return f"{sql_field} >= '{date1}'"
                elif date2:
                    return f"{sql_field} <= '{date2}'"
        
        # Verifica se é uma data única (formato: YYYY-MM-DD)
        elif re.match(r'^\d{4}-\d{2}-\d{2}
    
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
    
    # Métodos auxiliares para cálculo de datas
    @staticmethod
    def _get_current_week():
        """Retorna início e fim da semana atual (segunda a domingo)"""
        today = datetime.now().date()
        start = today - timedelta(days=today.weekday())
        end = start + timedelta(days=6)
        return start, end
    
    @staticmethod
    def _get_last_week():
        """Retorna início e fim da semana passada"""
        today = datetime.now().date()
        start = today - timedelta(days=today.weekday() + 7)
        end = start + timedelta(days=6)
        return start, end
    
    @staticmethod
    def _get_current_month():
        """Retorna início e fim do mês atual"""
        today = datetime.now().date()
        start = today.replace(day=1)
        # Último dia do mês
        if today.month == 12:
            end = today.replace(year=today.year + 1, month=1, day=1) - timedelta(days=1)
        else:
            end = today.replace(month=today.month + 1, day=1) - timedelta(days=1)
        return start, end
    
    @staticmethod
    def _get_last_month():
        """Retorna início e fim do mês passado"""
        today = datetime.now().date()
        first_day_current = today.replace(day=1)
        last_day_previous = first_day_current - timedelta(days=1)
        start = last_day_previous.replace(day=1)
        return start, last_day_previous
    
    @staticmethod
    def _get_current_quarter():
        """Retorna início e fim do trimestre atual"""
        today = datetime.now().date()
        quarter = (today.month - 1) // 3
        start_month = quarter * 3 + 1
        start = today.replace(month=start_month, day=1)
        end_month = start_month + 2
        if end_month > 12:
            end = today.replace(year=today.year + 1, month=1, day=1) - timedelta(days=1)
        else:
            end = today.replace(month=end_month + 1, day=1) - timedelta(days=1)
        return start, end
    
    @staticmethod
    def _get_last_quarter():
        """Retorna início e fim do trimestre passado"""
        today = datetime.now().date()
        current_quarter = (today.month - 1) // 3
        if current_quarter == 0:
            start = today.replace(year=today.year - 1, month=10, day=1)
            end = today.replace(year=today.year - 1, month=12, day=31)
        else:
            start_month = (current_quarter - 1) * 3 + 1
            start = today.replace(month=start_month, day=1)
            end = today.replace(month=start_month + 3, day=1) - timedelta(days=1)
        return start, end
    
    @staticmethod
    def _get_current_year():
        """Retorna início e fim do ano atual"""
        today = datetime.now().date()
        start = today.replace(month=1, day=1)
        end = today.replace(month=12, day=31)
        return start, end
    
    @staticmethod
    def _get_last_year():
        """Retorna início e fim do ano passado"""
        today = datetime.now().date()
        start = today.replace(year=today.year - 1, month=1, day=1)
        end = today.replace(year=today.year - 1, month=12, day=31)
        return start, end
, value):
            return f"{sql_field} = '{value}'"
        
        # Verifica se é formato especial do Metabase (ex: "2024-01-01T00:00:00")
        elif re.match(r'^\d{4}-\d{2}-\d{2}T', value):
            # Extrai apenas a data
            date_part = value.split('T')[0]
            return f"{sql_field} = '{date_part}'"
        
        # Verifica se é um range com formato especial (ex: "between:2024-01-01~2024-01-31")
        elif value.startswith("between:"):
            range_part = value.replace("between:", "")
            if "~" in range_part:
                dates = range_part.split("~")
                if len(dates) == 2:
                    return f"{sql_field} BETWEEN '{dates[0]}' AND '{dates[1]}'"
        
        # Formato não reconhecido
        else:
            print(f"   ⚠️ Formato de data não reconhecido: {value}")
            # Tenta usar como está (pode ser um formato válido SQL)
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
    
    # Métodos auxiliares para cálculo de datas
    @staticmethod
    def _get_current_week():
        """Retorna início e fim da semana atual (segunda a domingo)"""
        today = datetime.now().date()
        start = today - timedelta(days=today.weekday())
        end = start + timedelta(days=6)
        return start, end
    
    @staticmethod
    def _get_last_week():
        """Retorna início e fim da semana passada"""
        today = datetime.now().date()
        start = today - timedelta(days=today.weekday() + 7)
        end = start + timedelta(days=6)
        return start, end
    
    @staticmethod
    def _get_current_month():
        """Retorna início e fim do mês atual"""
        today = datetime.now().date()
        start = today.replace(day=1)
        # Último dia do mês
        if today.month == 12:
            end = today.replace(year=today.year + 1, month=1, day=1) - timedelta(days=1)
        else:
            end = today.replace(month=today.month + 1, day=1) - timedelta(days=1)
        return start, end
    
    @staticmethod
    def _get_last_month():
        """Retorna início e fim do mês passado"""
        today = datetime.now().date()
        first_day_current = today.replace(day=1)
        last_day_previous = first_day_current - timedelta(days=1)
        start = last_day_previous.replace(day=1)
        return start, last_day_previous
    
    @staticmethod
    def _get_current_quarter():
        """Retorna início e fim do trimestre atual"""
        today = datetime.now().date()
        quarter = (today.month - 1) // 3
        start_month = quarter * 3 + 1
        start = today.replace(month=start_month, day=1)
        end_month = start_month + 2
        if end_month > 12:
            end = today.replace(year=today.year + 1, month=1, day=1) - timedelta(days=1)
        else:
            end = today.replace(month=end_month + 1, day=1) - timedelta(days=1)
        return start, end
    
    @staticmethod
    def _get_last_quarter():
        """Retorna início e fim do trimestre passado"""
        today = datetime.now().date()
        current_quarter = (today.month - 1) // 3
        if current_quarter == 0:
            start = today.replace(year=today.year - 1, month=10, day=1)
            end = today.replace(year=today.year - 1, month=12, day=31)
        else:
            start_month = (current_quarter - 1) * 3 + 1
            start = today.replace(month=start_month, day=1)
            end = today.replace(month=start_month + 3, day=1) - timedelta(days=1)
        return start, end
    
    @staticmethod
    def _get_current_year():
        """Retorna início e fim do ano atual"""
        today = datetime.now().date()
        start = today.replace(month=1, day=1)
        end = today.replace(month=12, day=31)
        return start, end
    
    @staticmethod
    def _get_last_year():
        """Retorna início e fim do ano passado"""
        today = datetime.now().date()
        start = today.replace(year=today.year - 1, month=1, day=1)
        end = today.replace(year=today.year - 1, month=12, day=31)
        return start, end
