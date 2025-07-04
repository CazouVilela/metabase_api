#!/usr/bin/env python3
"""
Testes básicos da API
"""

import sys
import os
import json

# Adiciona diretório raiz ao path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def test_imports():
    """Testa se todos os módulos podem ser importados"""
    print("🧪 Testando imports...")
    
    try:
        # API modules
        from api import (
            MetabaseClient,
            FiltrosCaptura,
            FiltrosNormalizacao,
            ConsultaMetabase,
            ProcessadorJSON,
            ProcessadorTransformacao,
            ProcessadorAgregacao
        )
        print("✅ Imports da API: OK")
        
        # Proxy modules
        from proxy_server import create_app, PROXY_PORT
        print("✅ Imports do Proxy: OK")
        
        return True
        
    except ImportError as e:
        print(f"❌ Erro de import: {e}")
        return False

def test_filtros():
    """Testa módulos de filtros"""
    print("\n🧪 Testando filtros...")
    
    try:
        from api.filtros_normalizacao import FiltrosNormalizacao
        from api.filtros_captura import FiltrosCaptura
        
        # Teste de normalização
        nome_normalizado = FiltrosNormalizacao.normalizar_nome_parametro('posição')
        assert nome_normalizado == 'posicao', f"Esperado 'posicao', obtido '{nome_normalizado}'"
        print("✅ Normalização de nomes: OK")
        
        # Teste de validação de caracteres especiais
        validacao = FiltrosNormalizacao.validar_caracteres_especiais('Teste + Com & Especiais')
        assert validacao['tem_especiais'] == True
        assert '+' in validacao['caracteres']
        assert '&' in validacao['caracteres']
        print("✅ Validação de caracteres especiais: OK")
        
        # Teste de formatação para Metabase
        filtros = {'campanha': 'Teste', 'conta': ['Valor1', 'Valor2']}
        formatados = FiltrosCaptura.formatar_para_metabase(filtros)
        assert len(formatados) == 2
        assert formatados[0]['type'] == 'string/='
        assert isinstance(formatados[1]['value'], list)
        print("✅ Formatação para Metabase: OK")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro nos testes de filtros: {e}")
        return False

def test_processamento():
    """Testa módulos de processamento"""
    print("\n🧪 Testando processamento de dados...")
    
    try:
        from api.processamentoDados_json import ProcessadorJSON
        from api.processamentoDados_transformacao import ProcessadorTransformacao
        from api.processamentoDados_agregacao import ProcessadorAgregacao
        
        # Dados de teste
        dados_teste = [
            {'nome': 'Produto A', 'valor': 100, 'categoria': 'Cat1'},
            {'nome': 'Produto B', 'valor': 200, 'categoria': 'Cat1'},
            {'nome': 'Produto C', 'valor': 150, 'categoria': 'Cat2'}
        ]
        
        # Teste ProcessadorJSON
        resultado = ProcessadorJSON.preparar_para_tabela_virtual(dados_teste)
        assert 'dados' in resultado
        assert 'colunas' in resultado
        assert resultado['total_linhas'] == 3
        print("✅ ProcessadorJSON: OK")
        
        # Teste ProcessadorTransformacao
        dados_transformados = ProcessadorTransformacao.adicionar_campos_calculados(
            dados_teste.copy(),
            {'valor_com_taxa': 'valor * 1.1'}
        )
        assert 'valor_com_taxa' in dados_transformados[0]
        assert dados_transformados[0]['valor_com_taxa'] == 110
        print("✅ ProcessadorTransformacao: OK")
        
        # Teste ProcessadorAgregacao
        metricas = {
            'total_valor': {'campo': 'valor', 'operacao': 'soma'},
            'media_valor': {'campo': 'valor', 'operacao': 'media'}
        }
        resultado_metricas = ProcessadorAgregacao.calcular_metricas(dados_teste, metricas)
        assert resultado_metricas['total_valor'] == 450
        assert resultado_metricas['media_valor'] == 150
        print("✅ ProcessadorAgregacao: OK")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro nos testes de processamento: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_flask_app():
    """Testa criação da aplicação Flask"""
    print("\n🧪 Testando aplicação Flask...")
    
    try:
        from proxy_server import create_app
        
        app = create_app()
        assert app is not None
        print("✅ Criação da aplicação: OK")
        
        # Testa rotas básicas
        with app.test_client() as client:
            # Teste health check
            response = client.get('/health')
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['status'] == 'healthy'
            print("✅ Health check: OK")
            
            # Teste rota principal
            response = client.get('/')
            assert response.status_code == 200
            print("✅ Rota principal: OK")
            
            # Teste debug de filtros
            response = client.get('/api/debug/filters?teste=valor')
            assert response.status_code == 200
            data = json.loads(response.data)
            assert 'filtros_capturados' in data
            print("✅ Debug de filtros: OK")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro nos testes Flask: {e}")
        import traceback
        traceback.print_exc()
        return False

def run_all_tests():
    """Executa todos os testes"""
    print("=" * 60)
    print("🚀 TESTES DA NOVA ESTRUTURA")
    print("=" * 60)
    
    tests = [
        test_imports,
        test_filtros,
        test_processamento,
        test_flask_app
    ]
    
    results = []
    for test in tests:
        results.append(test())
    
    print("\n" + "=" * 60)
    print("📊 RESUMO DOS TESTES")
    print("=" * 60)
    
    total = len(results)
    passed = sum(results)
    failed = total - passed
    
    print(f"Total: {total}")
    print(f"✅ Passou: {passed}")
    print(f"❌ Falhou: {failed}")
    
    if failed == 0:
        print("\n🎉 TODOS OS TESTES PASSARAM!")
        return 0
    else:
        print(f"\n⚠️  {failed} teste(s) falharam")
        return 1

if __name__ == '__main__':
    sys.exit(run_all_tests())
