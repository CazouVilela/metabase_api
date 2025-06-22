import requests
from api.config import METABASE_BASE_URL, METABASE_USERNAME, METABASE_PASSWORD

def get_session_token():
    resp = requests.post(f"{METABASE_BASE_URL}/api/session", json={
        "username": METABASE_USERNAME,
        "password": METABASE_PASSWORD
    })
    resp.raise_for_status()
    return resp.json()['id']

def get_card_info(question_id, session_token):
    url = f"{METABASE_BASE_URL}/api/card/{question_id}"
    headers = {"X-Metabase-Session": session_token}
    resp = requests.get(url, headers=headers)
    resp.raise_for_status()
    return resp.json()


def build_parameters(filters, template_tags):
    params = []
    for key, value in filters.items():
        if key not in template_tags:
            continue
        tag = template_tags[key]
        param_type = tag.get("type", "category")
        params.append({
            "type": param_type,
            "target": ["variable", ["template-tag", key]],
            "value": value
        })
    return params


def query_question(question_id, parameters):
    session_token = get_session_token()
    card = get_card_info(question_id, session_token)
    template_tags = card.get("dataset_query", {}).get("native", {}).get("template-tags", {})

    if not isinstance(parameters, dict):
        parameters = {}

    built_params = build_parameters(parameters, template_tags)

    url = f"{METABASE_BASE_URL}/api/card/{question_id}/query"
    headers = {"X-Metabase-Session": session_token}

    resp = requests.post(url, json={"parameters": built_params}, headers=headers)
    resp.raise_for_status()
    result = resp.json()

    if isinstance(result, dict) and "data" in result:
        return result["data"]
    return result
