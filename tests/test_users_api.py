import pytest

from app.main import create_app


@pytest.fixture
def client(tmp_path):
    return create_app(tmp_path / "users.sqlite3").test_client()


def test_user_lifecycle(client):
    assert client.get("/health").json == {"service": "user-service", "status": "ok"}
    assert client.get("/users").json == []
    result = client.post("/users", json={"email": " Ivan@Example.COM ", "name": " Иван "})
    assert result.status_code == 201
    user = result.json
    assert user["email"] == "ivan@example.com" and user["name"] == "Иван"
    assert user["created_at"].endswith("Z")
    url = result.headers["Location"]
    assert client.get(url).json == user
    assert client.get("/users").json == [user]
    changed = client.put(url, json={"email": "other@example.com", "name": "Новое имя"})
    assert changed.status_code == 200
    assert changed.json == dict(user, email="other@example.com", name="Новое имя")
    deleted = client.delete(url)
    assert deleted.status_code == 204 and deleted.data == b""
    assert client.get(url).status_code == 404
    assert client.delete(url).status_code == 404
    assert client.get("/users").json == []


@pytest.mark.parametrize("payload", [[], {}, {"email": "wrong", "name": "Иван"},
                                     {"email": "a@b.example", "name": " "},
                                     {"email": "a@b.example", "name": "я" * 101}])
def test_invalid_user_payload(client, payload):
    assert client.post("/users", json=payload).status_code == 400
    assert client.put("/users/1", json=payload).json["code"] == "invalid_input"
    assert client.get("/users").json == []


def test_conflicts_are_atomic(client):
    first = client.post("/users", json={"email": "a@example.com", "name": "Первый"})
    second = client.post("/users", json={"email": "b@example.com", "name": "Второй"})
    assert client.post("/users", json={"email": "A@example.com", "name": "Дубль"}).status_code == 409
    change = client.put(second.headers["Location"], json={"email": first.json["email"], "name": "Дубль"})
    assert change.status_code == 409 and change.json["code"] == "duplicate_email"
    assert client.get(second.headers["Location"]).json == second.json


@pytest.mark.parametrize("user_id", [12, 2**63])
def test_unknown_user(client, user_id):
    url = f"/users/{user_id}"
    assert client.get(url).json["code"] == "user_not_found"
    assert client.put(url, json={"email": "a@example.com", "name": "Имя"}).status_code == 404
    assert client.delete(url).status_code == 404


def test_reopening_database_preserves_user(tmp_path):
    path = tmp_path / "users.sqlite3"
    result = create_app(path).test_client().post("/users", json={"email": "a@example.com", "name": "Имя"})
    assert create_app(path).test_client().get(result.headers["Location"]).json == result.json
