import sqlite3
from contextlib import closing, contextmanager
from datetime import datetime, timezone
from pathlib import Path


class DuplicateEmail(Exception):
    """Адрес уже зарегистрирован."""


class UserRepository:
    def __init__(self, path: Path):
        self.path = path
        path.parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as db:
            db.execute("""CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT NOT NULL UNIQUE,
                name TEXT NOT NULL,
                created_at TEXT NOT NULL
            )""")

    @contextmanager
    def connect(self):
        with closing(sqlite3.connect(self.path)) as db:
            db.row_factory = sqlite3.Row
            with db:
                yield db

    def create(self, email: str, name: str) -> dict:
        created_at = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
        try:
            with self.connect() as db:
                row = db.execute(
                    "INSERT INTO users (email, name, created_at) VALUES (?, ?, ?) RETURNING *",
                    (email, name, created_at),
                ).fetchone()
                return dict(row)
        except sqlite3.IntegrityError as error:
            raise DuplicateEmail from error

    def list_all(self) -> list[dict]:
        with self.connect() as db:
            return [dict(row) for row in db.execute("SELECT * FROM users ORDER BY id")]

    def get(self, user_id: int) -> dict | None:
        with self.connect() as db:
            row = db.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
            return dict(row) if row is not None else None

    def update(self, user_id: int, email: str, name: str) -> dict | None:
        try:
            with self.connect() as db:
                row = db.execute(
                    "UPDATE users SET email = ?, name = ? WHERE id = ? RETURNING *",
                    (email, name, user_id),
                ).fetchone()
                return dict(row) if row is not None else None
        except sqlite3.IntegrityError as error:
            raise DuplicateEmail from error

    def delete(self, user_id: int) -> bool:
        with self.connect() as db:
            return db.execute("DELETE FROM users WHERE id = ?", (user_id,)).rowcount == 1
