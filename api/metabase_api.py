import requests
from api.config import METABASE_BASE_URL, METABASE_USERNAME, METABASE_PASSWORD

def get_metabase_session():
    """
    Autentica no Metabase e retorna o token de sessão.
    """
    response = requests.post(f"{METABASE_BASE_URL}/api/session", json={
        "username": METABASE_USERNAME,
        "password": METABASE_PASSWORD
    })
    response.raise_for_status()
    return response.json()['id']

def query_question(question_id, params):
    """
    Consulta a API do Metabase para uma pergunta específica,
    com parâmetros de filtro formatados corretamente.
    """
    token = get_metabase_session()

    # Converte dict simples em formato de lista de parâmetros do Metabase
    parameters = [
        {
            "type": "string/=",
            "target": ["variable", ["template-tag", key]],
            "value": value
        }
        for key, value in params.items()
    ]

    response = requests.post(
        f"{METABASE_BASE_URL}/api/card/{question_id}/query/json",
        headers={"X-Metabase-Session": token},
        json={"parameters": parameters}
    )
    response.raise_for_status()
    return response.json()
