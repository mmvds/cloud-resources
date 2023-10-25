import requests
import json
from src.core.config import app_settings


def get_request(endpoint, params: dict | None = None) -> dict | list:
    params = params or {}
    headers = {
        'Content-Type': 'application/json',
    }
    params['token'] = app_settings.user_token

    response = requests.get(app_settings.api_base_url + endpoint, headers=headers, params=params)
    return response.json()


def post_request(endpoint, data, params: dict | None = None) -> list:
    params = params or {}
    headers = {
        'Content-Type': 'application/json',
    }
    params['token'] = app_settings.user_token

    response = requests.post(app_settings.api_base_url + endpoint, headers=headers, data=json.dumps(data),
                             params=params)
    return response.json()


def put_request(endpoint, m_id, data, params: dict | None = None) -> str:
    params = params or {}
    headers = {
        'Content-Type': 'application/json',
    }
    params['token'] = app_settings.user_token

    response = requests.put(f'{app_settings.api_base_url}{endpoint}/{m_id}', headers=headers, data=json.dumps(data),
                            params=params)
    return response.text


def delete_request(endpoint, m_id, params: dict | None = None) -> int:
    params = params or {}
    headers = {
        'Content-Type': 'application/json',
    }
    params['token'] = app_settings.user_token

    response = requests.delete(f'{app_settings.api_base_url}{endpoint}/{m_id}', headers=headers, params=params)
    return response.status_code
