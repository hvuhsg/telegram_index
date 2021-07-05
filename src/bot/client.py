import requests

protocol = "http://"
server_address = "127.0.0.1:8000"
server_url = protocol + server_address
REQUEST_TIMEOUT = 10


def get_suggestions_by_user_id(user_id: int) -> list:
    try:
        response = requests.get(server_url+"/suggestions", params={"count": 50, "uid": user_id}, timeout=REQUEST_TIMEOUT)
    except requests.exceptions.Timeout:
        return None
    if response.status_code != 200:
        return []
    suggestions = response.json()["suggestions"]
    return suggestions


def submit_user_action(user_id: int, post_id: int, saved: bool):
    try:
        response = requests.post(
            server_url+"/post/user_action",
            params={"uid": user_id, "post_id": post_id, "action": int(saved)},
            timeout=REQUEST_TIMEOUT
        )
    except requests.exceptions.Timeout:
        return None
    return response.status_code == 200


def load_saved_posts(user_id: int):
    try:
        response = requests.get(
            server_url+"/user/saved",
            params={"uid": user_id},
            timeout=REQUEST_TIMEOUT
        )
    except requests.exceptions.Timeout:
        return None
    if response.status_code != 200:
        return None
    return response.json()["posts"]
