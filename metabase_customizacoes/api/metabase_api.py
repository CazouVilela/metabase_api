import requests
from .config import METABASE_BASE_URL, METABASE_API_TOKEN


def query_question(question_id, params=None):
    headers = {"X-Metabase-Session": METABASE_API_TOKEN}
    url = f"{METABASE_BASE_URL}/api/card/{question_id}/query/json"
    body = {}
    if params:
        body["parameters"] = [
            {
                "type": "category",
                "target": ["variable", ["template-tag", key]],
                "value": value,
            }
            for key, value in params.items()
        ]
    resp = requests.post(url, json=body, headers=headers)
    resp.raise_for_status()
    return resp.json()
