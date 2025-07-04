#!/usr/bin/env python3
"""
Teste específico para o problema do action_type_filter
"""

import sys
sys.path.insert(0, '.')

from api.query_extractor import query_extractor

def teste_action_type():
    print("\n🔍 TESTE DO TEMPLATE TAG action_type_filter")
    print("=" * 60)
    
    # Query de exemplo com o problema
    query_exemplo = """
    WITH selected_action_types AS (
      SELECT action_type 
      FROM road.view_conversions_action_types_list
      WHERE {{action_type_filter}}
    )
    SELECT * FROM base_data
    WHERE 1=1
    [[AND {{conta}}]]
    [[AND {{campanha}}]]
    """
    
    print("\n📄 Query original:")
    print(query_exemplo)
    
    # Teste 1: Sem filtros
    print("\n1️⃣ Teste sem filtros:")
    query_processada = query_extractor.substituir_template_tags(query_exemplo, {})
    print("\n📄 Query processada:")
    print(query_processada)
    
    # Verifica se removeu corretamente
    if "{{" in query_processada:
        print("\n❌ ERRO: Ainda há template tags na query!")
    else:
        print("\n✅ OK: Todos os template tags foram removidos!")
    
    # Teste 2: Com filtro de conta
    print("\n\n2️⃣ Teste com filtro de conta:")
    filtros = {'conta': 'ASSOCIACAO DOS LOJISTAS'}
    query_processada2 = query_extractor.substituir_template_tags(query_exemplo, filtros)
    print("\n📄 Query processada:")
    print(query_processada2)
    
    # Verifica resultado
    if "{{" in query_processada2:
        print("\n❌ ERRO: Ainda há template tags na query!")
    else:
        print("\n✅ OK: Todos os template tags foram removidos!")

if __name__ == "__main__":
    # Limpa cache primeiro
    query_extractor.limpar_cache()
    
    teste_action_type()
