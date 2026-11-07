import os
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from dotenv import load_dotenv
from models import db, User, Transaction, Goal
import ai_bot

load_dotenv()

CATEGORIES = {
    "expense": ["Еда", "Транспорт", "Жильё", "Развлечения", "Здоровье", "Учёба", "Другое"],
    "income": ["Стипендия", "Зарплата", "Подработка", "Подарок", "Другое"],
}


def create_app(config=None):
    app = Flask(__name__)
    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-secret-change-me")
    app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL", "sqlite:///finance.db")
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    if config:
        app.config.update(config)

    db.init_app(app)
    login_manager = LoginManager(app)
    login_manager.login_view = "login"

    @login_manager.user_loader
    def load_user(uid):
        return db.session.get(User, int(uid))

    with app.app_context():
        db.create_all()

    # Авторизация 
    @app.route("/register", methods=["GET", "POST"])
    def register():
        if request.method == "POST":
            name = request.form["name"].strip()
            email = request.form["email"].strip().lower()
            password = request.form["password"]
            if not name or not email or len(password) < 6:
                flash("Заполните все поля, пароль - минимум 6 символов.")
            elif User.query.filter_by(email=email).first():
                flash("Такой email уже зарегистрирован.")
            else:
                u = User(name=name, email=email)
                u.set_password(password)
                db.session.add(u)
                db.session.commit()
                login_user(u)
                return redirect(url_for("index"))
        return render_template("auth.html", mode="register")

    @app.route("/login", methods=["GET", "POST"])
    def login():
        if request.method == "POST":
            u = User.query.filter_by(email=request.form["email"].strip().lower()).first()
            if u and u.check_password(request.form["password"]):
                login_user(u)
                return redirect(url_for("index"))
            flash("Неверный email или пароль.")
        return render_template("auth.html", mode="login")

    @app.route("/logout")
    @login_required
    def logout():
        logout_user()
        return redirect(url_for("login"))

    # Основные страницы 
    @app.route("/")
    @login_required
    def index():
        txs = (Transaction.query.filter_by(user_id=current_user.id)
               .order_by(Transaction.date.desc(), Transaction.id.desc()).limit(20).all())
        goals = Goal.query.filter_by(user_id=current_user.id).all()
        return render_template("index.html", summary=ai_bot.build_summary(current_user),
                               txs=txs, goals=goals, categories=CATEGORIES, today=date.today().isoformat())

    @app.route("/transactions", methods=["POST"])
    @login_required
    def add_transaction():
        try:
            amount = Decimal(request.form["amount"].replace(",", "."))
            d = datetime.strptime(request.form["date"], "%Y-%m-%d").date()
            kind = request.form["kind"]
            if amount <= 0 or kind not in CATEGORIES:
                raise ValueError
        except (InvalidOperation, ValueError, KeyError):
            flash("Проверьте сумму, дату и тип операции.")
            return redirect(url_for("index"))
        db.session.add(Transaction(user_id=current_user.id, kind=kind, amount=amount, date=d,
                                   category=request.form.get("category", "Другое"),
                                   note=request.form.get("note", "")[:200]))
        db.session.commit()
        return redirect(url_for("index"))

    @app.route("/transactions/<int:tid>/delete", methods=["POST"])
    @login_required
    def delete_transaction(tid):
        t = Transaction.query.filter_by(id=tid, user_id=current_user.id).first_or_404()
        db.session.delete(t)
        db.session.commit()
        return redirect(url_for("index"))

    @app.route("/goals", methods=["POST"])
    @login_required
    def add_goal():
        try:
            target = Decimal(request.form["target"].replace(",", "."))
            if target <= 0:
                raise ValueError
        except (InvalidOperation, ValueError, KeyError):
            flash("Укажите корректную сумму цели.")
            return redirect(url_for("index"))
        db.session.add(Goal(user_id=current_user.id, title=request.form["title"].strip()[:120] or "Цель", target=target))
        db.session.commit()
        return redirect(url_for("index"))

    @app.route("/goals/<int:gid>/add", methods=["POST"])
    @login_required
    def goal_add(gid):
        g = Goal.query.filter_by(id=gid, user_id=current_user.id).first_or_404()
        try:
            g.saved = g.saved + Decimal(request.form["amount"].replace(",", "."))
            db.session.commit()
        except (InvalidOperation, KeyError):
            flash("Некорректная сумма.")
        return redirect(url_for("index"))

    # API 
    @app.route("/api/summary")
    @login_required
    def api_summary():
        return jsonify(ai_bot.build_summary(current_user))

    @app.route("/api/chat", methods=["POST"])
    @login_required
    def api_chat():
        msg = (request.get_json(silent=True) or {}).get("message", "").strip()
        if not msg:
            return jsonify({"reply": "Напишите вопрос."}), 400
        return jsonify({"reply": ai_bot.reply(current_user, msg)})

    return app


if __name__ == "__main__":
    create_app().run(debug=True, port=5000)
