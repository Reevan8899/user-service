import os
import re
from pathlib import Path

from flask import Flask, jsonify, request
from waitress import serve

from app.storage import DuplicateEmail, UserRepository

EMAIL = re.compile(r"[^\s@]+@[^\s@]+\.[^\s@]+")
MAX_ID = 2**63 - 1


def user_fields(data: object) -> tuple[str, str]:
    if not isinstance(data, dict):
        raise ValueError("Передайте JSON-объект с полями email и name.")
    email, name = data.get("email"), data.get("name")
    if not isinstance(email, str):
        raise ValueError("Укажите корректный email.")
    email = email.strip().casefold()
    if len(email) > 254 or not EMAIL.fullmatch(email):
        raise ValueError("Укажите корректный email.")
    if not isinstance(name, str) or not 1 <= len(name.strip()) <= 100:
        raise ValueError("Имя должно содержать от 1 до 100 символов.")
    return email, name.strip()


def create_app(database: str | Path | None = None) -> Flask:
    app = Flask(__name__)
    app.json.ensure_ascii = False
    repository = UserRepository(Path(database or os.environ.get("USER_DB_PATH", "data/users.sqlite3")))

    @app.errorhandler(DuplicateEmail)
    def email_conflict(error):
        return jsonify(error="Этот email уже зарегистрирован.", code="duplicate_email"), 409

    def missing(user_id):
        return jsonify(error=f"Пользователь {user_id} не найден.", code="user_not_found"), 404

    @app.get("/health")
    def health():
        return jsonify(status="ok", service="user-service")

    @app.post("/users")
    def create_user():
        try:
            email, name = user_fields(request.get_json(silent=True))
        except ValueError as error:
            return jsonify(error=str(error), code="invalid_input"), 400
        user = repository.create(email, name)
        return jsonify(user), 201, {"Location": f"/users/{user['id']}"}

    @app.get("/users")
    def list_users():
        return jsonify(repository.list_all())

    @app.get("/users/<int:user_id>")
    def get_user(user_id):
        user = repository.get(user_id) if user_id <= MAX_ID else None
        return jsonify(user) if user is not None else missing(user_id)

    @app.put("/users/<int:user_id>")
    def update_user(user_id):
        try:
            email, name = user_fields(request.get_json(silent=True))
        except ValueError as error:
            return jsonify(error=str(error), code="invalid_input"), 400
        user = repository.update(user_id, email, name) if user_id <= MAX_ID else None
        return jsonify(user) if user is not None else missing(user_id)

    @app.delete("/users/<int:user_id>")
    def delete_user(user_id):
        if user_id <= MAX_ID and repository.delete(user_id):
            return "", 204
        return missing(user_id)

    return app


if __name__ == "__main__":
    serve(create_app(), host=os.environ.get("HOST", "127.0.0.1"), port=int(os.environ.get("PORT", "5001")))
