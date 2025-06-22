import requests
from api.config import METABASE_BASE_URL, METABASE_USERNAME, METABASE_PASSWORD

def get_session_token():
    resp = requests.post(f"{METABASE_BASE_URL}/api/session", json={
        "username": METABASE_USERNAME,
        "password": METABASE_PASSWORD
    })
    resp.raise_for_status()
    return resp.json()['id']

def query_question(question_id, parameters):
    session_token = get_session_token()
    url = f"{METABASE_BASE_URL}/api/card/{question_id}/query/json"
    headers = {
        "X-Metabase-Session": session_token
    }

    if not isinstance(parameters, dict):
        parameters = {}

    resp = requests.post(url, json={"parameters": parameters}, headers=headers)
    resp.raise_for_status()
    return resp.json()
