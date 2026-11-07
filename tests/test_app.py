from datetime import date
TODAY = date.today().isoformat()
import pytest
from app import create_app


@pytest.fixture
def client(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    app = create_app({"TESTING": True, "SQLALCHEMY_DATABASE_URI": "sqlite://"})
    with app.test_client() as c:
        yield c


def register(c):
    return c.post("/register", data={"name": "Kira", "email": "k@test.kz", "password": "secret1"},
                  follow_redirects=True)


def test_register_and_dashboard(client):
    r = register(client)
    assert r.status_code == 200 and "Баланс" in r.get_data(as_text=True)


def test_requires_login(client):
    assert client.get("/").status_code == 302


def test_add_transactions_and_summary(client):
    register(client)
    client.post("/transactions", data={"kind": "income", "category": "Стипендия", "amount": "100000", "date": TODAY})
    client.post("/transactions", data={"kind": "expense", "category": "Еда", "amount": "25000", "date": TODAY})
    data = client.get("/api/summary").get_json()
    assert data["income"] == 100000 and data["expense"] == 25000 and data["balance"] == 75000


def test_invalid_amount_rejected(client):
    register(client)
    client.post("/transactions", data={"kind": "expense", "category": "Еда", "amount": "-5", "date": TODAY})
    assert client.get("/api/summary").get_json()["expense"] == 0


def test_chatbot_local(client):
    register(client)
    client.post("/transactions", data={"kind": "income", "category": "Зарплата", "amount": "200000", "date": TODAY})
    r = client.post("/api/chat", json={"message": "какой у меня баланс?"})
    assert "200 000" in r.get_json()["reply"]


def test_goal_progress(client):
    register(client)
    client.post("/goals", data={"title": "Ноутбук", "target": "400000"})
    client.post("/goals/1/add", data={"amount": "50000"})
    assert client.get("/api/summary").get_json()["goals"][0]["saved"] == 50000
