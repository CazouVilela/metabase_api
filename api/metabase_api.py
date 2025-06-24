import requests
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

    # limpa parâmetros vazios
    parameters = [
        p for p in params
        if p.get("value") not in (None, "", [], {})
    ]

    print("📦 Parâmetros enviados ao Metabase:", parameters)

    resp = requests.post(
        f"{METABASE_BASE_URL}/api/card/{question_id}/query/json",
        headers={"X-Metabase-Session": token},
        json={"parameters": parameters},
        timeout=120,
    )

    if resp.status_code >= 400:
        print("🛑 Erro na resposta do Metabase")
        print("Status code:", resp.status_code)
        print("Resposta bruta:", resp.text)

    resp.raise_for_status()
    return resp.json()
