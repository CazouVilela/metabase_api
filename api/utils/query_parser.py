"""
Parser para queries SQL do Metabase com suporte dinâmico para filtros de data

Comportamento dos filtros de data:

PASSADO (past/last):
- Sem flag (~): períodos completos anteriores, excluindo o período atual
  - past7days: últimos 7 dias (não inclui hoje)
  - past2weeks: 2 semanas completas anteriores (Dom-Sáb), excluindo semana atual
  - past3months: 3 meses completos anteriores, excluindo mês atual
  
- Com flag (~): períodos completos anteriores + período atual
  - past7days~: últimos 7 dias incluindo hoje
  - past2weeks~: 2 semanas completas + semana atual completa
  - past3months~: 3 meses completos + mês atual completo

FUTURO (next):
- Sem flag (~): começa no próximo período
  - next7days: próximos 7 dias (começa amanhã)
  - next2weeks: 2 semanas completas começando no próximo domingo
  - next3months: 3 meses completos começando no próximo mês
  
- Com flag (~): inclui período atual + períodos futuros
  - next7days~: hoje + próximos 7 dias (total 8 dias)
  - next2weeks~: semana atual + próximas 2 semanas completas
  - next3months~: mês atual + próximos 3 meses completos

Casos especiais:
- thisday = hoje
- tomorrow = amanhã
- yesterday = ontem
- thisweek/month/quarter/year = período atual completo
- lastweek/month/quarter/year = período anterior completo
- nextweek/month/quarter/year = próximo período completo
"""

import re
from typing import Dict, List, Any, Tuple, Optional
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

class QueryParser:
    """Processa e transforma queries SQL"""
    
    # Mapeamento de campos para colunas SQL
    FIELD_MAPPING = {
        'data': 'date',
        'conta': 'account_name',
        'campanha': 'campaign_name',
        'adset': 'adset_name',
        'ad_name': 'ad_name',
        'anuncio': 'ad_name',
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
    
    # Mapeamento de unidades de tempo para cálculo
    TIME_UNITS = {
        'day': 'days',
        'days': 'days',
        'week': 'weeks',
        'weeks': 'weeks',
        'month': 'months',
        'months': 'months',
        'quarter': 'quarters',
        'quarters': 'quarters',
        'year': 'years',
        'years': 'years',
        'hour': 'hours',
        'hours': 'hours',
        'minute': 'minutes',
        'minutes': 'minutes'
    }
    

    def apply_filters(self, query: str, filters: Dict[str, Any]) -> str:
        """Substitui template tags pelos valores dos filtros"""
        query_processed = query
    
        print(f"\n🔧 Substituindo template tags:")
        print(f"   Filtros recebidos: {list(filters.keys())}")
    
        # Processa cada filtro disponível
        for filter_name, value in filters.items():
            if not value:
                continue
            
            # Obtém o nome do campo SQL (pode ser mapeado)
            sql_field_name = self.FIELD_MAPPING.get(filter_name, filter_name)
        
            # Tenta com o nome original primeiro
            pattern = f"[[AND {{{{{filter_name}}}}}]]"
            pattern_found = False
        
            # Verifica se o padrão existe na query
            if pattern in query_processed:
                pattern_found = True
            # Se não encontrar, tenta com o nome mapeado (se for diferente)
            elif sql_field_name != filter_name:
                pattern_mapped = f"[[AND {{{{{sql_field_name}}}}}]]"
                if pattern_mapped in query_processed:
                    pattern = pattern_mapped  # Usa o padrão mapeado
                    pattern_found = True
                    print(f"   🔄 Usando mapeamento: {filter_name} → {sql_field_name}")
        
            if pattern_found:
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
    
    def _parse_relative_date(self, value: str) -> Optional[Tuple[datetime, datetime]]:
        """
        Parse dinâmico de filtros relativos de data
        
        Comportamento padrão (sem ~):
        - past3days: últimos 3 dias (contando de hoje)
        - past2weeks: 2 semanas completas anteriores (excluindo a semana atual)
        - past3months: 3 meses completos anteriores (excluindo o mês atual)
        - past2quarters: 2 trimestres completos anteriores (excluindo o trimestre atual)
        - past2years: 2 anos completos anteriores (excluindo o ano atual)
        
        Com flag de inclusão (~):
        - past3days~: últimos 3 dias (mesmo comportamento, dias não têm "período completo")
        - past2weeks~: 2 semanas completas anteriores + semana atual completa
        - past3months~: 3 meses completos anteriores + mês atual completo
        - past2quarters~: 2 trimestres completos anteriores + trimestre atual completo
        - past2years~: 2 anos completos anteriores + ano atual completo
        """
        original_value = value
        value = value.lower().strip()
        
        # Detecta se tem flag de inclusão (~ no final)
        include_current = False
        if value.endswith('~'):
            include_current = True
            value = value[:-1]  # Remove o ~
            print(f"   📌 Flag de inclusão detectada (~) - incluir período atual")
        
        # Padrões para detectar filtros relativos
        # past/last/next + número + unidade
        pattern = r'^(past|last|next|previous)(\d+)(day|days|week|weeks|month|months|quarter|quarters|year|years|hour|hours|minute|minutes)$'
        match = re.match(pattern, value)
        
        if match:
            direction = match.group(1)
            number = int(match.group(2))
            unit = match.group(3)
            
            # Normaliza a unidade para o formato esperado
            normalized_unit = self.TIME_UNITS.get(unit, unit)
            
            print(f"   📅 Filtro dinâmico detectado: {direction} {number} {normalized_unit}")
            
            now = datetime.now()
            
            # Calcula as datas baseado na direção
            if direction in ['past', 'last', 'previous']:
                # Para períodos passados
                if normalized_unit == 'days':
                    # Para dias, a flag de inclusão significa incluir hoje
                    if include_current:
                        # Inclui hoje
                        start_date = (now - timedelta(days=number-1)).date()
                        end_date = now.date()
                    else:
                        # Não inclui hoje (ontem para trás)
                        start_date = (now - timedelta(days=number)).date()
                        end_date = (now - timedelta(days=1)).date()
                        
                elif normalized_unit in ['hours', 'minutes']:
                    # Para horas e minutos, mantém comportamento simples
                    delta_kwargs = {normalized_unit: number}
                    start_date = (now - timedelta(**delta_kwargs)).date()
                    end_date = now.date()
                    
                elif normalized_unit == 'weeks':
                    # Semanas completas (domingo a sábado)
                    if include_current:
                        # Inclui a semana atual completa
                        days_since_sunday = (now.weekday() + 1) % 7
                        current_week_start = now.date() - timedelta(days=days_since_sunday)
                        current_week_end = current_week_start + timedelta(days=6)
                        # Volta N semanas do início da semana atual
                        start_date = current_week_start - timedelta(weeks=number)
                        end_date = current_week_end
                    else:
                        # N semanas completas anteriores (excluindo a atual)
                        days_since_sunday = (now.weekday() + 1) % 7
                        last_week_end = now.date() - timedelta(days=days_since_sunday + 1)  # Sábado passado
                        start_date = last_week_end - timedelta(weeks=number) + timedelta(days=1)  # Domingo N semanas atrás
                        end_date = last_week_end
                        
                elif normalized_unit == 'months':
                    # Meses completos
                    if include_current:
                        # Inclui o mês atual completo
                        current_month_start = now.replace(day=1).date()
                        # Último dia do mês atual
                        if now.month == 12:
                            current_month_end = now.replace(year=now.year + 1, month=1, day=1).date() - timedelta(days=1)
                        else:
                            current_month_end = now.replace(month=now.month + 1, day=1).date() - timedelta(days=1)
                        # Volta N meses do início do mês atual
                        start_date = (current_month_start - relativedelta(months=number))
                        end_date = current_month_end
                    else:
                        # N meses completos anteriores (excluindo o atual)
                        # Primeiro dia do mês atual
                        first_of_current_month = now.replace(day=1).date()
                        # Último dia do mês anterior
                        last_month_end = first_of_current_month - timedelta(days=1)
                        # Primeiro dia N meses atrás
                        start_date = (last_month_end.replace(day=1) - relativedelta(months=number-1))
                        end_date = last_month_end
                        
                elif normalized_unit == 'quarters':
                    # Trimestres completos
                    if include_current:
                        # Inclui o trimestre atual completo
                        quarter = (now.month - 1) // 3
                        current_quarter_start = now.replace(month=quarter * 3 + 1, day=1).date()
                        # Fim do trimestre atual
                        end_month = quarter * 3 + 3
                        if end_month > 12:
                            current_quarter_end = now.replace(year=now.year + 1, month=1, day=1).date() - timedelta(days=1)
                        else:
                            current_quarter_end = now.replace(month=end_month + 1, day=1).date() - timedelta(days=1)
                        # Volta N trimestres
                        start_date = (current_quarter_start - relativedelta(months=number * 3))
                        end_date = current_quarter_end
                    else:
                        # N trimestres completos anteriores (excluindo o atual)
                        current_quarter = (now.month - 1) // 3
                        # Início do trimestre atual
                        current_quarter_start = now.replace(month=current_quarter * 3 + 1, day=1).date()
                        # Último dia do trimestre anterior
                        last_quarter_end = current_quarter_start - timedelta(days=1)
                        # Calcula qual trimestre é o anterior
                        if current_quarter == 0:
                            # Estamos no Q1, trimestre anterior é Q4 do ano passado
                            start_of_last_quarter = datetime(now.year - 1, 10, 1).date()
                        else:
                            # Trimestre anterior no mesmo ano
                            start_of_last_quarter = now.replace(month=(current_quarter - 1) * 3 + 1, day=1).date()
                        # Agora volta N-1 trimestres adicionais
                        start_date = (start_of_last_quarter - relativedelta(months=(number - 1) * 3))
                        end_date = last_quarter_end
                        
                elif normalized_unit == 'years':
                    # Anos completos
                    if include_current:
                        # Inclui o ano atual completo
                        current_year_start = now.replace(month=1, day=1).date()
                        current_year_end = now.replace(month=12, day=31).date()
                        # Volta N anos
                        start_date = current_year_start.replace(year=current_year_start.year - number)
                        end_date = current_year_end
                    else:
                        # N anos completos anteriores (excluindo o atual)
                        # Último dia do ano anterior
                        last_year_end = now.replace(month=12, day=31, year=now.year - 1).date()
                        # Primeiro dia N anos atrás
                        start_date = now.replace(month=1, day=1, year=now.year - number).date()
                        end_date = last_year_end
                            
            elif direction == 'next':
                # Para períodos futuros
                if normalized_unit == 'days':
                    # Para dias futuros
                    if include_current:
                        # Inclui hoje + próximos N dias
                        # next1days~ = hoje + amanhã (2 dias total)
                        # next7days~ = hoje + próximos 7 dias (8 dias total)
                        start_date = now.date()
                        end_date = (now + timedelta(days=number)).date()
                    else:
                        # Próximos N dias começando amanhã
                        # next1days = apenas amanhã
                        # next7days = amanhã até 7 dias depois (7 dias total)
                        start_date = (now + timedelta(days=1)).date()
                        end_date = (now + timedelta(days=number)).date()
                        
                elif normalized_unit in ['hours', 'minutes']:
                    # Para horas e minutos, comportamento simples
                    delta_kwargs = {normalized_unit: number}
                    start_date = now.date()
                    end_date = (now + timedelta(**delta_kwargs)).date()
                    
                elif normalized_unit == 'weeks':
                    # Semanas futuras
                    if include_current:
                        # Inclui a semana atual completa + próximas N semanas
                        days_since_sunday = (now.weekday() + 1) % 7
                        current_week_start = now.date() - timedelta(days=days_since_sunday)
                        # Adiciona N semanas ao domingo atual
                        end_week_start = current_week_start + timedelta(weeks=number)
                        start_date = current_week_start
                        end_date = end_week_start + timedelta(days=6)  # Sábado da última semana
                    else:
                        # N semanas completas começando no próximo domingo
                        days_until_sunday = 6 - now.weekday()  # Python: 0=segunda, 6=domingo
                        if days_until_sunday <= 0:  # Se hoje é domingo, próximo domingo é em 7 dias
                            days_until_sunday += 7
                        next_sunday = now.date() + timedelta(days=days_until_sunday)
                        # N semanas completas a partir do próximo domingo
                        end_week_start = next_sunday + timedelta(weeks=number-1)
                        start_date = next_sunday
                        end_date = end_week_start + timedelta(days=6)  # Sábado da última semana
                        
                elif normalized_unit == 'months':
                    # Meses futuros
                    if include_current:
                        # Inclui o mês atual completo + próximos N meses
                        current_month_start = now.replace(day=1).date()
                        # Adiciona N meses ao mês atual
                        future_date = now + relativedelta(months=number)
                        # Último dia do mês futuro
                        if future_date.month == 12:
                            future_month_end = future_date.replace(year=future_date.year + 1, month=1, day=1).date() - timedelta(days=1)
                        else:
                            future_month_end = future_date.replace(month=future_date.month + 1, day=1).date() - timedelta(days=1)
                        start_date = current_month_start
                        end_date = future_month_end
                    else:
                        # N meses completos começando no próximo mês
                        if now.month == 12:
                            next_month_start = now.replace(year=now.year + 1, month=1, day=1).date()
                        else:
                            next_month_start = now.replace(month=now.month + 1, day=1).date()
                        # Adiciona N-1 meses ao próximo mês
                        future_date = next_month_start + relativedelta(months=number-1)
                        # Último dia do mês futuro
                        if future_date.month == 12:
                            future_month_end = future_date.replace(year=future_date.year + 1, month=1, day=1) - timedelta(days=1)
                        else:
                            future_month_end = future_date.replace(month=future_date.month + 1, day=1) - timedelta(days=1)
                        start_date = next_month_start
                        end_date = future_month_end
                        
                elif normalized_unit == 'quarters':
                    # Trimestres futuros
                    if include_current:
                        # Inclui o trimestre atual + próximos N trimestres
                        quarter = (now.month - 1) // 3
                        current_quarter_start = now.replace(month=quarter * 3 + 1, day=1).date()
                        # Calcula o fim do trimestre N trimestres no futuro (incluindo o atual)
                        # Se N=1 e estamos no Q3, queremos o fim do Q3
                        # Se N=2 e estamos no Q3, queremos o fim do Q4
                        end_quarter = quarter + number - 1
                        end_year = now.year
                        while end_quarter > 3:
                            end_quarter -= 4
                            end_year += 1
                        # Último mês do trimestre final
                        end_month = (end_quarter * 3) + 3
                        if end_month == 12:
                            future_quarter_end = datetime(end_year, 12, 31).date()
                        else:
                            future_quarter_end = datetime(end_year, end_month + 1, 1).date() - timedelta(days=1)
                        start_date = current_quarter_start
                        end_date = future_quarter_end
                    else:
                        # N trimestres completos começando no próximo trimestre
                        current_quarter = (now.month - 1) // 3
                        if current_quarter == 3:  # Q4
                            next_quarter_start = datetime(now.year + 1, 1, 1).date()
                            start_year = now.year + 1
                            start_quarter = 0
                        else:
                            next_quarter_start = now.replace(month=(current_quarter + 1) * 3 + 1, day=1).date()
                            start_year = now.year
                            start_quarter = current_quarter + 1
                        
                        # Calcula o fim do último trimestre
                        end_quarter = start_quarter + number - 1
                        end_year = start_year
                        while end_quarter > 3:
                            end_quarter -= 4
                            end_year += 1
                        
                        # Último mês do trimestre final
                        end_month = (end_quarter * 3) + 3
                        if end_month == 12:
                            future_quarter_end = datetime(end_year, 12, 31).date()
                        else:
                            future_quarter_end = datetime(end_year, end_month + 1, 1).date() - timedelta(days=1)
                        
                        start_date = next_quarter_start
                        end_date = future_quarter_end
                        
                elif normalized_unit == 'years':
                    # Anos futuros
                    if include_current:
                        # Inclui o ano atual + próximos N anos
                        # next1years~ = 2025 completo + 2026 completo
                        current_year_start = now.replace(month=1, day=1).date()
                        future_year_end = now.replace(year=now.year + number, month=12, day=31).date()
                        start_date = current_year_start
                        end_date = future_year_end
                    else:
                        # N anos completos começando no próximo ano
                        # next1years = apenas 2026 completo
                        # next2years = 2026 e 2027 completos
                        next_year_start = now.replace(year=now.year + 1, month=1, day=1).date()
                        # Corrigido: ano atual + N (não +1 +N)
                        last_year = now.year + number
                        future_year_end = datetime(last_year, 12, 31).date()
                        start_date = next_year_start
                        end_date = future_year_end
            else:
                return None
                
            # Adiciona informação de debug sobre os dias da semana e período
            weekdays = ['Seg', 'Ter', 'Qua', 'Qui', 'Sex', 'Sáb', 'Dom']
            start_weekday = weekdays[start_date.weekday()]
            end_weekday = weekdays[end_date.weekday()]
            
            # Calcula total de dias no período
            total_days = (end_date - start_date).days + 1
            
            # Mensagem de debug específica por tipo de período
            if normalized_unit == 'days':
                if direction == 'next':
                    if include_current:
                        msg = f" (hoje + {number} dias futuros)"
                    else:
                        msg = f" (começando amanhã)"
                else:
                    msg = " (incluindo hoje)" if include_current else ""
                print(f"   📊 Datas calculadas: {start_date} ({start_weekday}) até {end_date} ({end_weekday})")
                print(f"      → {total_days} dias{msg}")
            elif normalized_unit == 'weeks':
                total_weeks = total_days // 7
                if direction == 'next':
                    if include_current:
                        msg = f" (semana atual + {number} semanas futuras)"
                    else:
                        msg = f" ({number} semanas começando no próximo domingo)"
                else:
                    msg = " + semana atual" if include_current else ""
                print(f"   📊 Datas calculadas: {start_date} ({start_weekday}) até {end_date} ({end_weekday})")
                print(f"      → {total_weeks} semanas completas ({total_days} dias){msg}")
            elif normalized_unit == 'months':
                if direction == 'next':
                    msg = " + mês atual" if include_current else " (começando no próximo mês)"
                else:
                    msg = " + mês atual" if include_current else ""
                print(f"   📊 Datas calculadas: {start_date} até {end_date}")
                print(f"      → Meses completos ({total_days} dias){msg}")
            elif normalized_unit == 'quarters':
                if direction == 'next':
                    msg = " + trimestre atual" if include_current else " (começando no próximo trimestre)"
                else:
                    msg = " + trimestre atual" if include_current else ""
                print(f"   📊 Datas calculadas: {start_date} até {end_date}")
                print(f"      → Trimestres completos ({total_days} dias){msg}")
            elif normalized_unit == 'years':
                if direction == 'next':
                    msg = " + ano atual" if include_current else " (começando no próximo ano)"
                else:
                    msg = " + ano atual" if include_current else ""
                print(f"   📊 Datas calculadas: {start_date} até {end_date}")
                print(f"      → Anos completos ({total_days} dias){msg}")
            else:
                print(f"   📊 Datas calculadas: {start_date} ({start_weekday}) até {end_date} ({end_weekday})")
                print(f"      → {total_days} dias")
            
            return (start_date, end_date)
        
        # Casos especiais não dinâmicos
        special_cases = {
            'today': lambda: (datetime.now().date(), datetime.now().date()),
            'thisday': lambda: (datetime.now().date(), datetime.now().date()),  # Metabase usa thisday
            'yesterday': lambda: ((datetime.now() - timedelta(days=1)).date(), 
                                 (datetime.now() - timedelta(days=1)).date()),
            'tomorrow': lambda: ((datetime.now() + timedelta(days=1)).date(),
                                (datetime.now() + timedelta(days=1)).date()),
            'thisweek': lambda: self._get_current_week(),
            'lastweek': lambda: self._get_last_week(),
            'nextweek': lambda: self._get_next_week(),
            'thismonth': lambda: self._get_current_month(),
            'lastmonth': lambda: self._get_last_month(),
            'nextmonth': lambda: self._get_next_month(),
            'thisquarter': lambda: self._get_current_quarter(),
            'lastquarter': lambda: self._get_last_quarter(),
            'nextquarter': lambda: self._get_next_quarter(),
            'thisyear': lambda: self._get_current_year(),
            'lastyear': lambda: self._get_last_year(),
            'nextyear': lambda: self._get_next_year(),
            'alltime': lambda: (datetime(2000, 1, 1).date(), datetime.now().date()),
        }
        
        if value in special_cases:
            print(f"   📅 Filtro especial detectado: {value}")
            return special_cases[value]()
            
        return None
    
    def _build_date_clause(self, sql_field: str, value: str) -> str:
        """Constrói cláusula SQL para filtros de data"""
        
        # Se valor é None ou vazio, retorna vazio
        if not value:
            return ""
        
        # Converte para string se necessário
        value = str(value).strip()
        
        # Tenta fazer parse de filtro relativo dinâmico
        date_range = self._parse_relative_date(value)
        if date_range:
            start_date, end_date = date_range
            
            if start_date == end_date:
                return f"{sql_field} = '{start_date}'"
            else:
                return f"{sql_field} BETWEEN '{start_date}' AND '{end_date}'"
        
        # Verifica se é apenas ~ (tudo até hoje)
        elif value == "~":
            return f"{sql_field} <= '{datetime.now().date()}'"
        
        # Verifica se é um range (formato: data1~data2)
        elif "~" in value and not value.endswith('~'):
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
        elif re.match(r'^\d{4}-\d{2}-\d{2}$', value):
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
            # NÃO usa o valor diretamente para evitar erros SQL
            return ""
    
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
    
    # Métodos auxiliares para cálculo de datas especiais
    @staticmethod
    def _get_current_week():
        """Retorna início e fim da semana atual (domingo a sábado - padrão Metabase)"""
        today = datetime.now().date()
        # Calcula dias desde domingo (0 = segunda, 6 = domingo no Python)
        days_since_sunday = (today.weekday() + 1) % 7
        start = today - timedelta(days=days_since_sunday)
        end = start + timedelta(days=6)
        return start, end
    
    @staticmethod
    def _get_last_week():
        """Retorna início e fim da semana passada (domingo a sábado)"""
        today = datetime.now().date()
        days_since_sunday = (today.weekday() + 1) % 7
        # Domingo da semana passada
        start = today - timedelta(days=days_since_sunday + 7)
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
    def _get_next_week():
        """Retorna início e fim da próxima semana (domingo a sábado)"""
        today = datetime.now().date()
        # Python: 0=segunda, 6=domingo
        # Precisamos calcular dias até o próximo domingo
        days_until_sunday = 6 - today.weekday()  # Se hoje é segunda (0), faltam 6 dias para domingo
        if days_until_sunday <= 0:  # Se hoje é domingo (6), próximo domingo é em 7 dias
            days_until_sunday += 7
        next_sunday = today + timedelta(days=days_until_sunday)
        end = next_sunday + timedelta(days=6)
        return next_sunday, end
    
    @staticmethod
    def _get_next_month():
        """Retorna início e fim do próximo mês"""
        today = datetime.now().date()
        if today.month == 12:
            start = today.replace(year=today.year + 1, month=1, day=1)
            end = today.replace(year=today.year + 1, month=1, day=31)
        else:
            start = today.replace(month=today.month + 1, day=1)
            # Último dia do próximo mês
            if today.month + 1 == 12:
                end = today.replace(year=today.year + 1, month=1, day=1) - timedelta(days=1)
            else:
                end = today.replace(month=today.month + 2, day=1) - timedelta(days=1)
        return start, end
    
    @staticmethod
    def _get_next_quarter():
        """Retorna início e fim do próximo trimestre"""
        today = datetime.now().date()
        current_quarter = (today.month - 1) // 3
        
        if current_quarter == 3:  # Estamos no Q4
            start = today.replace(year=today.year + 1, month=1, day=1)
            end = today.replace(year=today.year + 1, month=3, day=31)
        else:
            start_month = (current_quarter + 1) * 3 + 1
            start = today.replace(month=start_month, day=1)
            end_month = start_month + 2
            if end_month == 12:
                end = today.replace(month=12, day=31)
            else:
                end = today.replace(month=end_month + 1, day=1) - timedelta(days=1)
        return start, end
    
    @staticmethod
    def _get_next_year():
        """Retorna início e fim do próximo ano"""
        today = datetime.now().date()
        start = today.replace(year=today.year + 1, month=1, day=1)
        end = today.replace(year=today.year + 1, month=12, day=31)
        return start, end
