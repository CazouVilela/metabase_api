import requests
import json
from api.config import (
    METABASE_BASE_URL,
    METABASE_USERNAME,
    METABASE_PASSWORD,
)

# ---------- sessão reutilizável ----------
_session_cache = None

def get_metabase_session() -> str:
    global _session_cache
    if _session_cache:
        return _session_cache

    resp = requests.post(
        f"{METABASE_BASE_URL}/api/session",
        json={"username": METABASE_USERNAME, "password": METABASE_PASSWORD},
        timeout=30,
    )
    resp.raise_for_status()
    _session_cache = resp.json()["id"]
    return _session_cache

# ---------- executa a questão ----------
def query_question(question_id: int, params: list):
    """
    Executa a questão *question_id* aplicando os parâmetros já formatados
    (lista de dicts contendo type, target e value exatamente como a API espera).
    """
    token = get_metabase_session()
    
    # Remove parâmetros vazios
    parameters = [
        p for p in params
        if p.get("value") not in (None, "", [], {})
    ]

    print("\n📦 Parâmetros enviados ao Metabase:")
    print(json.dumps(parameters, indent=2, ensure_ascii=False))
    
    # Monta o payload
    payload = {
        "parameters": parameters
    }
    
    print(f"\n🚀 POST para: {METABASE_BASE_URL}/api/card/{question_id}/query/json")
    
    resp = requests.post(
        f"{METABASE_BASE_URL}/api/card/{question_id}/query/json",
        headers={
            "X-Metabase-Session": token,
            "Content-Type": "application/json"
        },
        json=payload,
        timeout=120,
    )

    if resp.status_code >= 400:
        print("\n🛑 Erro na resposta do Metabase")
        print(f"   Status code: {resp.status_code}")
        print(f"   Resposta: {resp.text[:500]}")

    resp.raise_for_status()
    
    result = resp.json()
    
    # Log do resultado
    if isinstance(result, list):
        print(f"\n✅ Query executada: {len(result)} linhas retornadas")
    
    return result
