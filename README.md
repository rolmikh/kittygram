# Kittygram API

## Описание
Backend-приложение для управления котами, дуэлями и турнирами между котами. Система позволяет создавать котов, проводить дуэли, голосовать за участников, отслеживать результаты поединков и формировать рейтинг победителей.

Проект реализован на Django REST Framework и предоставляет REST API с JWT-аутентификацией, системой турниров, статистикой голосований и Docker-развертыванием.

## Технологии
- Python 3.13
- Django REST Framework

## Запуск проекта

1. Клонировать репозиторий:
```bash
git clone https://github.com/rolmikh/kittygram.git
```

2. Перейти в папку:
```bash
cd kittygram
```

3. Создать и активировать виртуальное окружение:
```bash
py -3.13 -m venv venv
```
```bash
venv\Scripts\activate
```

4. Установить зависимости из файла:
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

5. Создать .env файл:
```bash
copy .env.example .env
```

6. Применить миграции:
```bash
python manage.py migrate
```

7. Запустить сервер:
```bash
python manage.py runserver
```

---

## Запуск через Docker

Сборка и запуск:
```bash
docker-compose up --build
```

Приложение доступно:
http://127.0.0.1:8000/

---

## Документация API
Swagger:
http://127.0.0.1:8000/swagger/

---

## Аутентификация

Получение токена:

POST /auth/jwt/create/

Пример:
{
  "username": "user",
  "password": "password"
}

### Создание турнира
Запрос: 

POST /tournaments/

{
  "name": "Летний кубок"
}

Ответ:
{
    "id": 3,
    "name": "Летний кубок",
    "start_date": "2026-05-11T08:39:36.944540Z",
    "end_date": "2026-05-12T08:39:36.944540Z",
    "status": "active",
    "created_at": "2026-05-11T08:39:36.944871Z",
    "winner": null
}

### Создание дуэли
Запрос:

POST /duels/

{
  "first_cat": 4,
  "second_cat": 3,
  "tournament": 3
}

Ответ:
{
    "id": 9,
    "start_time": null,
    "end_time": null,
    "status": "planned",
    "is_draw": false,
    "created_at": "2026-05-11T08:40:18.637749Z",
    "first_cat": 4,
    "second_cat": 3,
    "tournament": 3,
    "winner": null
}

### Голосование
Запрос:

POST /duels/9/vote/

{
  "cat": 3
}

Ответ:
{
    "detail": "vote accepted"
}

## Основные возможности
- CRUD для моделей котов и достижений
- JWT-аутентификация
- Создание дуэлей между котами
- Запуск дуэлей и автоматическое изменение статусов
- Турниры между котами
- Подсчет победителей турниров
- Рейтинг котов и статистика дуэлей 
- Голосование за участников
- Фильтрация, поиск, сортировка
- Пагинация результатов  
- Документация API (Swagger)