# api/metabase_dataset.py
"""
Cliente para usar a API Dataset nativa do Metabase
Mesma API que o frontend usa - máxima performance
"""

import requests
import gzip
import json
from typing import Dict, Any, List, Optional
import time
from .metabase_client import metabase_client

class MetabaseDatasetClient:
    """Cliente para API Dataset do Metabase (mesma que o frontend usa)"""
    
    def __init__(self):
        self.client = metabase_client
        self.base_url = metabase_client.base_url
        
    def executar_dataset_query(
        self, 
        question_id: int, 
        parameters: Optional[List[Dict]] = None
    ) -> Dict[str, Any]:
        """
        Executa query usando a API Dataset nativa
        
        Esta é a MESMA API que o frontend do Metabase usa!
        
        Args:
            question_id: ID da questão
            parameters: Parâmetros formatados
            
        Returns:
            Resposta no formato nativo do Metabase
        """
        start_time = time.time()
        
        # Obtém token
        token = self.client.get_session_token()
        
        # Primeiro, obtém a query da pergunta
        question_info = self.client.get_question_info(question_id)
        
        # Prepara o payload no formato da API Dataset
        dataset_query = question_info.get('dataset_query', {})
        
        # Aplica parâmetros se fornecidos
        if parameters:
            if 'native' in dataset_query:
                # Query SQL nativa
                dataset_query['native']['template-tags'] = self._processar_template_tags(
                    dataset_query['native'].get('template-tags', {}),
                    parameters
                )
            else:
                # Query builder
                dataset_query['parameters'] = parameters
        
        # Payload completo
        payload = {
            'database': dataset_query.get('database'),
            'type': dataset_query.get('type', 'native'),
            'native' if dataset_query.get('type') == 'native' else 'query': 
                dataset_query.get('native' if dataset_query.get('type') == 'native' else 'query'),
            'parameters': parameters or [],
            'middleware': {
                'js-int-to-string?': True,
                'add-default-userland-constraints?': True
            }
        }
        
        print(f"\n🚀 [DATASET API] Executando query via API nativa")
        print(f"   Question ID: {question_id}")
        print(f"   Tipo: {dataset_query.get('type', 'native')}")
        print(f"   Database ID: {dataset_query.get('database')}")
        
        # Debug do payload
        print(f"\n📦 [DATASET API] Payload:")
        print(json.dumps(payload, indent=2)[:500] + "...")
        
        # Headers especiais para performance
        headers = {
            'X-Metabase-Session': token,
            'Content-Type': 'application/json',
            'Accept-Encoding': 'gzip, deflate',  # Solicita compressão
            'X-Metabase-Client': 'custom-iframe'  # Identificação
        }
        
        # Faz a requisição
        response = requests.post(
            f"{self.base_url}/api/dataset",
            headers=headers,
            json=payload,
            timeout=300
        )
        
        response.raise_for_status()
        
        # Processa resposta - automaticamente lida com gzip se presente
        result = response.json()
        
        elapsed = time.time() - start_time
        
        # Log de performance
        if 'data' in result:
            rows = len(result['data'].get('rows', []))
            print(f"✅ [DATASET API] {rows:,} linhas em {elapsed:.2f}s")
            print(f"   Velocidade: {rows/elapsed:.0f} linhas/s")
            
            # Informações adicionais
            if 'results_metadata' in result['data']:
                cols = len(result['data']['results_metadata'].get('columns', []))
                print(f"   Colunas: {cols}")
        elif 'rows' in result:
            # Formato alternativo
            rows = len(result.get('rows', []))
            print(f"✅ [DATASET API] {rows:,} linhas em {elapsed:.2f}s")
        else:
            print(f"⚠️  [DATASET API] Resposta sem dados. Estrutura:")
            print(json.dumps(list(result.keys()), indent=2))
        
        return result
    
    def _processar_template_tags(
        self, 
        template_tags: Dict, 
        parameters: List[Dict]
    ) -> Dict:
        """Processa template tags com parâmetros"""
        # Implementação simplificada
        # Na prática, precisaria mapear os parâmetros corretamente
        return template_tags
    
    def converter_para_formato_linha(self, dataset_result: Dict) -> List[Dict]:
        """
        Converte formato colunar do Metabase para formato de linha
        
        Args:
            dataset_result: Resultado da API Dataset
            
        Returns:
            Lista de dicionários (formato linha)
        """
        # Verifica diferentes estruturas possíveis
        if 'data' in dataset_result:
            data = dataset_result['data']
            rows = data.get('rows', [])
            cols = data.get('cols', [])
        elif 'rows' in dataset_result and 'cols' in dataset_result:
            # Formato direto
            rows = dataset_result.get('rows', [])
            cols = dataset_result.get('cols', [])
        else:
            print(f"⚠️  [CONVERTER] Estrutura não reconhecida:")
            print(json.dumps(list(dataset_result.keys()), indent=2))
            return []
        
        # Extrai nomes das colunas
        col_names = []
        if isinstance(cols, list) and len(cols) > 0:
            if isinstance(cols[0], dict):
                col_names = [col.get('name', f'col_{i}') for i, col in enumerate(cols)]
            else:
                # Se cols for lista simples de nomes
                col_names = cols
        
        # Se não conseguiu extrair nomes, usa índices
        if not col_names and rows and len(rows) > 0:
            col_names = [f'col_{i}' for i in range(len(rows[0]))]
        
        print(f"📊 [CONVERTER] Convertendo {len(rows)} linhas com {len(col_names)} colunas")
        
        # Converte para formato de linha
        result = []
        for row in rows:
            row_dict = {}
            for i, value in enumerate(row):
                if i < len(col_names):
                    row_dict[col_names[i]] = value
            result.append(row_dict)
        
        return result
    
    def executar_card_query(
        self, 
        question_id: int, 
        parameters: Optional[List[Dict]] = None
    ) -> List[Dict]:
        """
        Método alternativo: usa endpoint /api/card/:id/query
        Este é mais simples e pode ser mais confiável
        
        Args:
            question_id: ID da questão
            parameters: Parâmetros formatados
            
        Returns:
            Lista de dicionários (já no formato linha)
        """
        start_time = time.time()
        
        # Usa o método já existente do metabase_client
        resultado = self.client.execute_question(question_id, parameters or [])
        
        elapsed = time.time() - start_time
        
        if isinstance(resultado, list):
            print(f"✅ [CARD API] {len(resultado):,} linhas em {elapsed:.2f}s")
            print(f"   Velocidade: {len(resultado)/elapsed:.0f} linhas/s")
        
        return resultado

# Instância global
metabase_dataset_client = MetabaseDatasetClient()
