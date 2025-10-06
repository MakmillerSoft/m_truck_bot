# M-Truck Bot

## Deployment / Git

- `.env` не комітиться (див. `.gitignore`). Приклад у `.env.example`.
- SQLite база `data/truck_bot.db` відслідковується у git за вимогою.
- Початкова ініціалізація виконана: `git init`, перший коміт додано.

## Локальний запуск

1. Python 3.11+
2. Створити та активувати venv
3. `pip install -r requirements.txt`
4. Скопіювати `.env.example` у `.env` і заповнити `BOT_TOKEN`, `ADMIN_IDS` тощо
5. `python -m app.main`
