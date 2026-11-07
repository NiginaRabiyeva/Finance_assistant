"""AI-бот финансового помощника.
Если задан ANTHROPIC_API_KEY - отвечает Claude с учётом данных пользователя.
Иначе работает встроенный бот-аналитик (правила), чтобы проект запускался на любом ноутбуке."""
import os
from collections import defaultdict
from datetime import date
import requests
from models import Transaction, Goal


def build_summary(user):
    """Сводка за текущий месяц: доходы, расходы, баланс, расходы по категориям, цели."""
    today = date.today()
    start = today.replace(day=1)
    txs = Transaction.query.filter(Transaction.user_id == user.id, Transaction.date >= start).all()
    income = sum(float(t.amount) for t in txs if t.kind == "income")
    expense = sum(float(t.amount) for t in txs if t.kind == "expense")
    by_cat = defaultdict(float)
    for t in txs:
        if t.kind == "expense":
            by_cat[t.category] += float(t.amount)
    goals = [{"title": g.title, "target": float(g.target), "saved": float(g.saved)}
             for g in Goal.query.filter_by(user_id=user.id).all()]
    return {"income": income, "expense": expense, "balance": income - expense,
            "by_category": dict(by_cat), "goals": goals}


def _fmt(x):
    return f"{x:,.0f}".replace(",", " ")


def local_reply(summary, message):
    m = message.lower()
    inc, exp, bal = summary["income"], summary["expense"], summary["balance"]
    cats = sorted(summary["by_category"].items(), key=lambda kv: -kv[1])
    if "баланс" in m or "остал" in m:
        return f"Ваш баланс за месяц: {_fmt(bal)} ₸ (доходы {_fmt(inc)}, расходы {_fmt(exp)})."
    if "доход" in m:
        return f"Доходы за этот месяц: {_fmt(inc)} ₸."
    if "категор" in m or "куда" in m or "потрат" in m or "расход" in m:
        if not cats:
            return "Расходов в этом месяце пока нет."
        top = ", ".join(f"{c}: {_fmt(v)} ₸" for c, v in cats[:3])
        return f"Расходы за месяц: {_fmt(exp)} ₸. Больше всего ушло на: {top}."
    if "цел" in m or "накоп" in m:
        if not summary["goals"]:
            return "Целей пока нет. Добавьте первую цель накоплений в блоке «Цели»."
        g = summary["goals"][0]
        left = max(g["target"] - g["saved"], 0)
        return f"Цель «{g['title']}»: накоплено {_fmt(g['saved'])} из {_fmt(g['target'])} ₸, осталось {_fmt(left)} ₸."
    if "совет" in m or "эконом" in m or "помоги" in m:
        if inc <= 0:
            return "Добавьте доходы и расходы - и я дам персональные советы."
        rate = (inc - exp) / inc * 100
        tip = f"Вы откладываете {rate:.0f}% дохода. "
        tip += "Хороший ориентир - 20%. " if rate < 20 else "Отличный результат, так держать! "
        if cats:
            tip += f"Самая крупная статья расходов - «{cats[0][0]}» ({_fmt(cats[0][1])} ₸): начните оптимизацию с неё."
        return tip
    return "Я умею: показать баланс, доходы, расходы по категориям, прогресс целей и дать совет. Спросите, например: «дай совет»."


def claude_reply(summary, message):
    key = os.getenv("ANTHROPIC_API_KEY")
    system = ("Ты персональный финансовый помощник. Отвечай по-русски, кратко и дружелюбно, "
              "опираясь на данные пользователя. Данные за текущий месяц: " + str(summary))
    r = requests.post(
        "https://api.anthropic.com/v1/messages",
        headers={"x-api-key": key, "anthropic-version": "2023-06-01", "content-type": "application/json"},
        json={"model": os.getenv("ANTHROPIC_MODEL", "claude-sonnet-5-5"), "max_tokens": 500,
              "system": system, "messages": [{"role": "user", "content": message}]},
        timeout=30)
    r.raise_for_status()
    return r.json()["content"][0]["text"]


def reply(user, message):
    summary = build_summary(user)
    if os.getenv("ANTHROPIC_API_KEY"):
        try:
            return claude_reply(summary, message)
        except Exception:
            pass  # при ошибке сети/ключа падаем на локального бота
    return local_reply(summary, message)
