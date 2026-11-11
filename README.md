# user-service

[![CI](https://github.com/Reevan8899/user-service/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/Reevan8899/user-service/actions/workflows/ci.yml)

Практическая работа № 8. Сервис управляет пользователями и хранит их в SQLite. [Контракт API](docs/api-contract.md)

## Локальный запуск

Нужен Python 3.10+ со SQLite 3.35+.

```sh
python -m pip install -r requirements.txt
python -m app.main
```

`HOST` и `PORT` задают адрес прослушивания. По умолчанию `127.0.0.1:5001`. `USER_DB_PATH` задаёт путь SQLite, по умолчанию `data/users.sqlite3`.

## API

Локальный адрес сервиса `http://localhost:5001`. Запросы с телом используют `Content-Type: application/json`. Ответы с данными и ошибками имеют формат JSON в UTF-8. Успешное удаление возвращает пустое тело.

| Метод | Путь | Назначение | Коды ответа |
|---|---|---|---|
| POST | `/users` | Создать пользователя | 201, 400, 409 |
| GET | `/users` | Получить список по возрастанию ID | 200 |
| GET | `/users/{id}` | Получить пользователя | 200, 404 |
| PUT | `/users/{id}` | Заменить имя и адрес электронной почты | 200, 400, 404, 409 |
| DELETE | `/users/{id}` | Удалить пользователя | 204, 404 |
| GET | `/health` | Проверить живость HTTP-сервиса | 200 |

POST и PUT требуют объект с полями `email` и `name`. Email содержит имя, `@` и домен, нормализуется к нижнему регистру и уникален. Имя после удаления пробелов по краям содержит от 1 до 100 символов. Повторный email возвращает `409 Conflict`. `created_at` присваивается сервером в UTC и сохраняется при обновлении.

```json
{
  "id": 1,
  "email": "ivan@example.com",
  "name": "Иван Иванов",
  "created_at": "2026-11-11T12:00:00Z"
}
```

Список содержит массив объектов `User`. Ошибка имеет поля `error` и `code`, например `{"error":"Пользователь 42 не найден.","code":"user_not_found"}`. Проверка живости возвращает `{"status":"ok","service":"user-service"}`.

## Проверки и контейнер

```sh
python -m pip install -r requirements-dev.txt
python -m ruff check app tests
python -m pytest --cov=app --cov-report=term-missing --cov-fail-under=80
docker build -t user-service .
docker run --rm -p 5001:5001 user-service
```

CI собирает и публикует образы `ghcr.io/reevan8899/user-service` с тегами `latest` и `sha-<commit>`. Для приватного пакета GHCR используется авторизация владельца.

Для общего запуска используйте Compose из [order-service](https://github.com/Reevan8899/order-service).
