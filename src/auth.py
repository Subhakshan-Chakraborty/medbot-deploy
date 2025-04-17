from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
from src.models import db, User

auth = Blueprint("auth", __name__)

@auth.route('/signup', methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email")
        password = request.form.get("password")

        hashed_pw = generate_password_hash(password, method="pbkdf2:sha256")
        new_user = User(name=name, email=email, password=hashed_pw)
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for("auth.login"))
    return render_template("signup.html")

    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        user = User.query.filter_by(email=email).first()
        if user:
            flash("Email already exists.")
            return redirect(url_for("auth.signup"))

        new_user = User(email=email, password=generate_password_hash(password, method="pbkdf2:sha256"))
        db.session.add(new_user)
        db.session.commit()
        login_user(new_user)
        return redirect(url_for("index"))

    return render_template("signup.html")

@auth.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        user = User.query.filter_by(email=email).first()

        if not user or not check_password_hash(user.password, password):
            flash("Login failed. Check email and password.")
            return redirect(url_for("auth.login"))

        login_user(user)
        return redirect(url_for("index"))

    return render_template("login.html")

@auth.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("auth.login"))
