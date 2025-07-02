#!/usr/bin/env python3
"""
Força o frontend a usar Native Performance ao invés de Streaming
PARA DE USAR CHUNKS!
"""

import os
import sys
from pathlib import Path

def update_main_js():
    """Atualiza main.js para NUNCA usar streaming"""
    print("🔧 Atualizando main.js...")
    
    main_js = Path.home() / "metabase_customizacoes" / "componentes" / "tabela_virtual" / "js" / "main.js"
    
    with open(main_js, 'r') as f:
        content = f.read()
    
    # Força streaming = false
    replacements = [
        # Desabilita streaming no construtor
        ("this.useStreaming = false;", "this.useStreaming = false; // NUNCA! Metabase não usa!"),
        
        # Desabilita verificação de streaming
        ("this.useStreaming = Utils.getUrlParams().streaming === 'true';", 
         "this.useStreaming = false; // IGNORANDO parâmetro - Metabase não usa streaming!"),
        
        # Força shouldUseStreaming a retornar false
        ("const shouldStream = this.useStreaming || await this.shouldUseStreaming(filtros);",
         "const shouldStream = false; // NUNCA usa streaming - Metabase nativo não usa!"),
         
        # Muda log
        ("// Decide se usa streaming baseado no contexto",
         "// NUNCA usa streaming - Metabase nativo carrega tudo de uma vez!")
    ]
    
    for old, new in replacements:
        if old in content:
            content = content.replace(old, new)
            print(f"✓ Substituído: {old[:50]}...")
    
    # Salva
    with open(main_js, 'w') as f:
        f.write(content)
    
    print("✓ main.js atualizado")

def update_data_loader():
    """Atualiza data-loader.js para usar Native por padrão"""
    print("\n🔧 Atualizando data-loader.js...")
    
    data_loader = Path.home() / "metabase_customizacoes" / "componentes" / "tabela_virtual" / "js" / "data-loader.js"
    
    with open(data_loader, 'r') as f:
        content = f.read()
    
    # Adiciona método loadDataNativePerformance se não existir
    if "loadDataNativePerformance" not in content:
        print("⚠️  Método loadDataNativePerformance não encontrado!")
        print("   Você precisa adicionar o método do artifact ao data-loader.js")
    
    # Força buildUrl a usar native por padrão
    old_default = "buildUrl(questionId, filtros, useDirect = true)"
    new_default = "buildUrl(questionId, filtros, useNative = true)"
    
    if old_default in content:
        content = content.replace(old_default, new_default)
        print("✓ buildUrl atualizado para usar Native por padrão")
    
    # Salva
    with open(data_loader, 'w') as f:
        f.write(content)

def create_test_url():
    """Cria URL de teste"""
    print("\n📌 URLs para testar:")
    print("\n1. COM STREAMING (errado - lento):")
    print("   http://localhost:8080/metabase_customizacoes/componentes/tabela_virtual/?question_id=51&streaming=true")
    print("   ⏱️  Esperado: ~60 segundos")
    
    print("\n2. SEM STREAMING (correto - rápido):")
    print("   http://localhost:8080/metabase_customizacoes/componentes/tabela_virtual/?question_id=51")
    print("   ⏱️  Esperado: ~2-4 segundos")
    
    print("\n3. FORÇAR LEGACY (para comparar):")
    print("   http://localhost:8080/metabase_customizacoes/componentes/tabela_virtual/?question_id=51&performance=legacy")
    print("   ⏱️  Esperado: ~10-15 segundos")

def main():
    print("🚀 Forçando uso de Native Performance (sem chunks!)")
    print("=" * 60)
    
    update_main_js()
    update_data_loader()
    create_test_url()
    
    print("\n✅ Concluído!")
    print("\n⚠️  IMPORTANTE:")
    print("1. Limpe o cache do navegador (Ctrl+Shift+R)")
    print("2. Recarregue a página")
    print("3. Abra o console (F12) para ver os logs")
    print("\n🎯 Procure por:")
    print('   "🚀 [NATIVE PERFORMANCE] Carregando como Metabase nativo..."')
    print('   "✅ [NATIVE PERFORMANCE] 77,591 linhas"')
    print("\n❌ NÃO deve aparecer:")
    print('   "🌊 Iniciando carregamento com streaming..."')
    print('   "📦 [STREAMING] Chunk..."')

if __name__ == "__main__":
    main()
