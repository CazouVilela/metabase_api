#!/usr/bin/env python3
"""
Script para testar diferentes formatos de target para os parâmetros
Execute com: python test_target_formats.py
"""

import requests
import json
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from api.metabase_api import get_metabase_session, METABASE_BASE_URL

def test_parameter_formats():
    """Testa diferentes formatos de parâmetros"""
    
    print("🧪 TESTE DE FORMATOS DE TARGET\n")
    
    token = get_metabase_session()
    question_id = 51
    
    # Valores de teste
    campanha_value = "Road | Engajamento | Degusta Burger 2025 | 26/05"
    conta_value = "ASSOCIACAO DOS LOJISTAS DO SHOPPING CENTER DA BARRA"
    
    # Diferentes formatos de target para testar
    test_cases = [
        {
            "name": "Formato 1: template-tag (atual)",
            "parameters": [
                {
                    "type": "string/=",
                    "target": ["variable", ["template-tag", "campanha"]],
                    "value": [campanha_value]
                },
                {
                    "type": "string/=",
                    "target": ["variable", ["template-tag", "conta"]],
                    "value": [conta_value]
                }
            ]
        },
        {
            "name": "Formato 2: Só nome do parâmetro",
            "parameters": [
                {
                    "type": "string/=",
                    "target": ["variable", "campanha"],
                    "value": [campanha_value]
                },
                {
                    "type": "string/=",
                    "target": ["variable", "conta"],
                    "value": [conta_value]
                }
            ]
        },
        {
            "name": "Formato 3: dimension com field-id",
            "parameters": [
                {
                    "type": "string/=",
                    "target": ["dimension", ["template-tag", "campanha"]],
                    "value": [campanha_value]
                },
                {
                    "type": "string/=",
                    "target": ["dimension", ["template-tag", "conta"]],
                    "value": [conta_value]
                }
            ]
        },
        {
            "name": "Formato 4: Sem type, só value e target",
            "parameters": [
                {
                    "target": ["variable", ["template-tag", "campanha"]],
                    "value": campanha_value  # String simples
                },
                {
                    "target": ["variable", ["template-tag", "conta"]],
                    "value": conta_value
                }
            ]
        }
    ]
    
    # Também vamos testar descobrir o ID do campo
    print("🔍 Primeiro, vamos buscar informações sobre os campos...\n")
    
    # Busca metadata do database
    db_resp = requests.get(
        f"{METABASE_BASE_URL}/api/database/3/metadata",
        headers={"X-Metabase-Session": token},
        timeout=30
    )
    
    if db_resp.status_code == 200:
        db_data = db_resp.json()
        
        # Procura pelos campos campaign_name e account_name
        for table in db_data.get('tables', []):
            if 'metaads' in table.get('name', '').lower():
                print(f"\nTabela encontrada: {table.get('name')} (ID: {table.get('id')})")
                print("Campos relevantes:")
                
                for field in table.get('fields', []):
                    field_name = field.get('name', '').lower()
                    if any(term in field_name for term in ['campaign', 'account', 'campanha', 'conta']):
                        print(f"  • {field.get('name')} (ID: {field.get('id')})")
    
    print("\n" + "="*60)
    
    # Executa os testes
    for test in test_cases:
        print(f"\n{'='*60}")
        print(f"Testando: {test['name']}")
        print(f"{'='*60}")
        
        payload = {"parameters": test["parameters"]}
        
        print("\nPayload enviado:")
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        
        try:
            resp = requests.post(
                f"{METABASE_BASE_URL}/api/card/{question_id}/query/json",
                headers={
                    "X-Metabase-Session": token,
                    "Content-Type": "application/json"
                },
                json=payload,
                timeout=30
            )
            
            if resp.status_code == 200:
                data = resp.json()
                if isinstance(data, list):
                    rows_count = len(data)
                    print(f"\n{'✅' if rows_count < 5000 else '⚠️'} Retornou {rows_count} linhas")
                    
                    # Verifica se filtrou corretamente
                    if rows_count < 5000 and rows_count > 0:
                        # Verifica se os dados batem com o filtro
                        sample = data[0]
                        if 'campaign_name' in sample and 'account_name' in sample:
                            campaign_match = campanha_value in str(sample.get('campaign_name', ''))
                            account_match = conta_value in str(sample.get('account_name', ''))
                            
                            print(f"  Campanha filtrada corretamente: {'✅' if campaign_match else '❌'}")
                            print(f"  Conta filtrada corretamente: {'✅' if account_match else '❌'}")
                            
                            if campaign_match and account_match:
                                print("\n🎉 FORMATO CORRETO ENCONTRADO!")
                else:
                    print(f"\n⚠️  Resposta inesperada: {type(data)}")
            else:
                print(f"\n❌ Erro: Status {resp.status_code}")
                error_text = resp.text[:300]
                print(f"Erro: {error_text}")
                
                # Tenta extrair mensagem de erro
                try:
                    error_json = resp.json()
                    if 'message' in error_json:
                        print(f"Mensagem: {error_json['message']}")
                except:
                    pass
                
        except Exception as e:
            print(f"\n❌ Exceção: {str(e)}")


def inspect_dashboard_request():
    """Inspeciona como o dashboard faz requisições"""
    print("\n📊 COMO INSPECIONAR REQUISIÇÕES DO DASHBOARD:\n")
    
    print("""
1. Abra o dashboard no navegador
2. Abra o DevTools (F12) > Network
3. Limpe o Network (ícone 🚫)
4. Aplique um filtro no dashboard
5. Procure por requisições para '/api/card/*/query'
6. Clique na requisição e veja:
   - Request Headers
   - Request Payload (importante!)
   
7. O payload deve ter algo como:
   {
     "parameters": [...]
   }
   
8. Copie o formato exato dos parâmetros!
""")


if __name__ == "__main__":
    test_parameter_formats()
    inspect_dashboard_request()
