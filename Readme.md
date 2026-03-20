# PROJECT 3 - URL Shortener API

REST API сервис для сокращения ссылок.
Позволяет создавать короткие URL, выполнять редирект на оригинальные ссылки и управлять ссылками для зарегистрированных пользователей.

Сервис реализован на **FastAPI**, использует **SQLite** для хранения данных и **Redis** для кэширования.

---

# Функциональность

* регистрация пользователя
* авторизация пользователя
* создание коротких ссылок
* редирект по короткой ссылке
* получение информации о ссылке
* обновление ссылки
* удаление ссылки
* статистика переходов

Гостевые пользователи могут создавать ссылки, но управление доступно только владельцу.

---

# Используемые технологии
Python, FastAPI, SQLAlchemy, SQLite, Redis, Docker, Docker Compose

---

# Запуск проекта

## 1. Клонировать репозиторий

git clone ...
cd url-shortener

## 2. Запустить через Docker

docker compose up --build

После запуска API будет доступен по адресу:

http://localhost:8000

Интерфейс:

http://localhost:8000/docs


---

# Примеры запросов

## Регистрация пользователя

POST `/auth/register`

{
  "username": "MalyshevIvan",
  "email": "AI2025@example.com",
  "password": "12345678"
}

---

## Авторизация

POST `/auth/login`

username=test
password=12345678

Ответ содержит JWT токен для авторизации.

---

## Создание короткой ссылки

POST `/links/shorten`

{
  "original_url": "https://google.com/"
}

Ответ:

{
  "short_code": "abc123"
}

---

## Переход по короткой ссылке

GET /abc123

Происходит перенаправление на оригинальный URL.

---

# База данных

Используется **SQLite**.

## Таблица users

* id
* username
* email
* password_hash
* created_at

## Таблица links

* id
* original_url
* short_code
* created_at
* expires_at
* clicks
* owner_id

---

# Развернутый сервис

API доступен по ссылке:

https://project3-whc8.onrender.com



Документация:

https://project3-whc8.onrender.com/docs

---
---

# PROJECT 4 - Fast API testing

Были добавлены файлы для тестов и чуть-чуть изменен файл main.py (буквально пару строк)

---

Отчет покрытия
<img width="1236" height="340" alt="Screenshot 2026-03-20 at 14 29 20" src="https://github.com/user-attachments/assets/baaa1909-419b-4b1f-af63-9d3de2cedba2" />
---

Отчет нагрузки Locust со 100 пользователями и 7 spawnrate
<img width="1470" height="956" alt="Screenshot 2026-03-20 at 14 37 48" src="https://github.com/user-attachments/assets/e05ef82c-e6f8-4757-9b73-1678c0f7fee2" />
