# api/metabase_client.py
"""
Cliente para comunicação com a API do Metabase
"""

import requests
import json
from typing import Dict, List, Optional
from .config import (
    METABASE_BASE_URL,
    METABASE_USERNAME,
    METABASE_PASSWORD,
    API_TIMEOUT,
    API_MAX_RETRIES
)

class MetabaseClient:
    """Cliente para interagir com a API do Metabase"""
    
    def __init__(self):
        self._session_token = None
        self.base_url = METABASE_BASE_URL
        
    def get_session_token(self) -> str:
        """Obtém ou reutiliza token de sessão"""
        if self._session_token:
            return self._session_token
            
        response = requests.post(
            f"{self.base_url}/api/session",
            json={"username": METABASE_USERNAME, "password": METABASE_PASSWORD},
            timeout=30
        )
        response.raise_for_status()
        self._session_token = response.json()["id"]
        return self._session_token
    
    def execute_question(self, question_id: int, parameters: List[Dict]) -> List[Dict]:
        """
        Executa uma questão do Metabase com parâmetros
        
        Args:
            question_id: ID da questão no Metabase
            parameters: Lista de parâmetros formatados
            
        Returns:
            Lista de resultados (linhas)
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
            timeout=API_TIMEOUT
        )
        
        if response.status_code >= 400:
            print(f"\n🛑 Erro na resposta do Metabase: {response.status_code}")
            print(f"   Resposta: {response.text[:500]}")
            
        response.raise_for_status()
        result = response.json()
        
        if isinstance(result, list):
            print(f"✅ Query executada: {len(result):,} linhas retornadas")
            
        return result
    
    def get_question_info(self, question_id: int) -> Dict:
        """Obtém informações sobre uma questão"""
        token = self.get_session_token()
        
        response = requests.get(
            f"{self.base_url}/api/card/{question_id}",
            headers={"X-Metabase-Session": token},
            timeout=30
        )
        response.raise_for_status()
        
        return response.json()
    
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

# Instância global do cliente
metabase_client = MetabaseClient()
