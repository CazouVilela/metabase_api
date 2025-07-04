"""
Serviço para comunicação com a API do Metabase
"""

import requests
from typing import Dict, List, Optional
from config.settings import METABASE_CONFIG, API_CONFIG

class MetabaseService:
    """Cliente para interagir com a API do Metabase"""
    
    def __init__(self):
        self._session_token = None
        self.base_url = METABASE_CONFIG['url']
        self._query_cache = {}  # Cache de queries por question_id
        
    def get_session_token(self) -> str:
        """Obtém ou reutiliza token de sessão"""
        if self._session_token:
            return self._session_token
            
        response = requests.post(
            f"{self.base_url}/api/session",
            json={
                "username": METABASE_CONFIG['username'],
                "password": METABASE_CONFIG['password']
            },
            timeout=30
        )
        response.raise_for_status()
        self._session_token = response.json()["id"]
        return self._session_token
    
    def get_question_info(self, question_id: int) -> Dict:
        """Obtém informações completas sobre uma questão"""
        token = self.get_session_token()
        
        response = requests.get(
            f"{self.base_url}/api/card/{question_id}",
            headers={"X-Metabase-Session": token},
            timeout=30
        )
        response.raise_for_status()
        
        return response.json()
    
    def get_question_query(self, question_id: int) -> Dict:
        """
        Extrai a query SQL nativa de uma pergunta do Metabase
        Retorna dict com query e template tags
        """
        # Verifica cache
        if question_id in self._query_cache:
            print(f"📦 Query do cache para pergunta {question_id}")
            return self._query_cache[question_id]
        
        try:
            # Obtém informações da pergunta
            info = self.get_question_info(question_id)
            
            # Verifica se é uma query nativa
            dataset_query = info.get('dataset_query', {})
            if dataset_query.get('type') != 'native':
                raise ValueError(f"Pergunta {question_id} não é uma query SQL nativa")
            
            # Extrai a query e template tags
            native_query = dataset_query.get('native', {})
            query_sql = native_query.get('query', '')
            template_tags = native_query.get('template-tags', {})
            
            result = {
                'query': query_sql,
                'template_tags': list(template_tags.keys()),
                'question_name': info.get('name', ''),
                'database_id': info.get('database_id')
            }
            
            # Adiciona ao cache
            self._query_cache[question_id] = result
            
            print(f"✅ Query extraída: {len(query_sql)} caracteres, "
                  f"{len(result['template_tags'])} tags")
            
            return result
            
        except Exception as e:
            print(f"❌ Erro ao extrair query: {str(e)}")
            raise
    
    def execute_question(self, question_id: int, parameters: List[Dict]) -> List[Dict]:
        """
        Executa uma questão do Metabase com parâmetros
        (Mantido para compatibilidade, mas não é mais usado)
        """
        token = self.get_session_token()
        
        # Remove parâmetros vazios
        clean_parameters = [
            p for p in parameters
            if p.get("value") not in (None, "", [], {})
        ]
        
        print(f"\n📦 Executando questão {question_id} com {len(clean_parameters)} parâmetros")
        
        payload = {"parameters": clean_parameters}
        
        response = requests.post(
            f"{self.base_url}/api/card/{question_id}/query/json",
            headers={
                "X-Metabase-Session": token,
                "Content-Type": "application/json"
            },
            json=payload,
            timeout=API_CONFIG['timeout']
        )
        
        response.raise_for_status()
        result = response.json()
        
        if isinstance(result, list):
            print(f"✅ Query executada: {len(result):,} linhas retornadas")
            
        return result
    
    def get_database_metadata(self, database_id: int) -> Dict:
        """Obtém metadata do banco de dados"""
        token = self.get_session_token()
        
        response = requests.get(
            f"{self.base_url}/api/database/{database_id}/metadata",
            headers={"X-Metabase-Session": token},
            timeout=30
        )
        response.raise_for_status()
        
        return response.json()
    
    def clear_cache(self):
        """Limpa o cache de queries"""
        self._query_cache.clear()
        print("🗑️ Cache de queries do Metabase limpo")
