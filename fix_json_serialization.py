#!/usr/bin/env python3
"""
Script para corrigir o erro de serialização JSON no endpoint /api/query/native
"""

import re

# Lê o arquivo routes.py
with open('proxy_server/routes.py', 'r') as f:
    content = f.read()

# Adiciona imports necessários no topo se não existirem
if 'from datetime import datetime, date' not in content:
    # Encontra a linha dos imports
    import_section = re.search(r'(from flask import.*?\n)', content)
    if import_section:
        content = content.replace(
            import_section.group(0),
            import_section.group(0) + 'from datetime import datetime, date\nfrom decimal import Decimal\n'
        )

# Adiciona a função json_serial se não existir
if 'def json_serial' not in content:
    # Adiciona após os imports e antes da função register_routes
    insert_pos = content.find('def register_routes(app):')
    if insert_pos > 0:
        json_serial_func = '''
def json_serial(obj):
    """Serializador JSON para tipos especiais"""
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    elif isinstance(obj, Decimal):
        return float(obj)
    elif hasattr(obj, '__dict__'):
        return str(obj)
    raise TypeError(f"Type {type(obj)} not serializable")

'''
        content = content[:insert_pos] + json_serial_func + content[insert_pos:]

# Corrige o endpoint api_query_native
# Encontra a linha problemática
problem_line = 'json_str = json.dumps(response_data)'
if problem_line in content:
    content = content.replace(
        problem_line,
        'json_str = json.dumps(response_data, default=json_serial)'
    )
    print("✅ Corrigido: json.dumps agora usa json_serial para serialização")

# Salva o arquivo corrigido
with open('proxy_server/routes.py', 'w') as f:
    f.write(content)

print("✅ Arquivo proxy_server/routes.py corrigido com sucesso!")
print("🔄 Reinicie o servidor para aplicar as mudanças.")
