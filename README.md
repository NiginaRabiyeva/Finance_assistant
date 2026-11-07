# Персональный финансовый помощник (Flask + MySQL + AI-бот)

Учёт доходов и расходов, цели накоплений, график по категориям и AI-чат с советами.
Стек: Python 3.10+, Flask, SQLAlchemy, MySQL (или SQLite для быстрого старта), Chart.js.

## Быстрый запуск (macOS / Windows / Linux)

```bash
# 1. Виртуальное окружение
python3 -m venv venv                 # Windows: python -m venv venv
source venv/bin/activate             # Windows: venv\Scripts\activate

# 2. Зависимости
pip install -r requirements.txt

# 3. Настройки
cp .env.example .env                 # Windows: copy .env.example .env
```

### Вариант A - без MySQL (самый быстрый)
В `.env` оставьте `DATABASE_URL=sqlite:///finance.db`.

### Вариант B - MySQL через Docker
```bash
docker compose up -d
```
В `.env` используйте `DATABASE_URL=mysql+pymysql://finance_user:finance_pass@127.0.0.1:3306/finance_db`.

### Вариант C - свой MySQL (Workbench / XAMPP / brew)
Выполните `schema.sql`, затем впишите свои логин/пароль в `DATABASE_URL`.

### Запуск
```bash
python app.py
```
Откройте http://127.0.0.1:5000 и зарегистрируйтесь.
В VS Code: Run and Debug → «Flask: запуск приложения» (интерпретатор: Cmd/Ctrl+Shift+P → Python: Select Interpreter → venv).

### Тесты (показать в видео)
```bash
python -m pytest -v
```

## AI-бот
- Без ключа: встроенный бот-аналитик (баланс, расходы по категориям, цели, совет).
- С ключом: впишите `ANTHROPIC_API_KEY` в `.env`, и бот отвечает через Claude на основе ваших данных.

## Структура
| Файл | Назначение |
|---|---|
| `app.py` | Flask: маршруты, авторизация, API |
| `models.py` | Модели БД: User, Transaction, Goal |
| `ai_bot.py` | AI-бот и расчёт сводки |
| `templates/`, `static/` | Интерфейс |
| `schema.sql` | Схема MySQL |
| `tests/` | Автотесты |

---

# Шаблон под требования Видео № 3

| Что показать | Что говорить / показывать на экране |
|---|---|
| Запланированные работы | Список этапов: БД → авторизация → учёт операций → цели → AI-бот → тесты |
| Выполненные задачи | Всё, что реально сделано (отметьте галочками) |
| Разработанные модули | `models.py`, `app.py`, `ai_bot.py`, интерфейс |
| Первый прототип | Live-демо: регистрация → добавить доход/расход → график → цель → вопрос боту |
| Код / БД / интерфейс | Открыть `app.py`, таблицы в MySQL Workbench (`SELECT * FROM transactions;`) |
| Результаты тестирования | Запустить `pytest -v` (6 тестов) |
| Вклад участников | Каждый называет свою часть (см. таблицу ниже - заполните) |
| Проблемы | Напр.: настройка MySQL на разных ОС → решили SQLite-fallback и Docker |
| Риски | Безопасность данных (нет CSRF/HTTPS), зависимость AI от интернета и ключа, точность советов |
| Изменения плана | Напр.: добавили fallback-бота без внешнего API |
| Следующий этап | Бюджеты по категориям, экспорт CSV, прогноз расходов, CSRF-защита, деплой, UI-тесты |

| Участник | Роль | Что сделал |
|---|---|---|
| ... | Backend | ... |
| ... | Frontend | ... |
| ... | БД / тесты | ... |
| ... | AI-бот | ... |
