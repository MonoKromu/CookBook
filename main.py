import os
from datetime import timedelta

import requests
from flask import Flask, render_template, request, redirect, flash, get_flashed_messages
from flask_jwt_extended import JWTManager, set_access_cookies, set_refresh_cookies, get_jwt, jwt_required, \
    unset_jwt_cookies, verify_jwt_in_request

import api
from db.db_operations import DatabaseOperations
from forms.login import LoginForm
from forms.recipe import RecipeForm
from forms.register import RegisterForm

db = DatabaseOperations("db.sqlite")

app = Flask(__name__)
app.config['SECRET_KEY'] = 'my_secret_key'

app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY', 'dev-secret-key')
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(minutes=15)
app.config['JWT_REFRESH_TOKEN_EXPIRES'] = timedelta(days=7)
app.config['JWT_TOKEN_LOCATION'] = ['cookies', 'headers']
app.config['JWT_COOKIE_HTTPONLY'] = True
app.config['JWT_COOKIE_SAMESITE'] = 'Lax'
app.config['JWT_COOKIE_CSRF_PROTECT'] = True
app.config['JWT_CSRF_CHECK_FORM'] = True

jwt = JWTManager(app)


@jwt.expired_token_loader
def expired_token_callback(jwt_header, jwt_payload):
    response = requests.get("http://localhost:5000/api/refresh", cookies=request.cookies).json()
    if "access_token" not in response:
        return redirect("/logout")
    else:
        re = redirect(request.path)
        set_access_cookies(re, response.get("access_token"))
        return re


@app.route("/")
@app.route("/index")
def index():
    verify_jwt_in_request(optional=True)
    title = "Главная"
    return render_template("base.html", title=title, jwt=get_jwt())


@app.route("/register", methods=["GET", "POST"])
@jwt_required(optional=True)
def register():
    title = "Регистрация"
    form = RegisterForm()
    if form.validate_on_submit():
        response = requests.post("http://localhost:5000/api/register", json=dict(request.form)).json()
        if "success" in response:
            flash("Аккаунт создан")
            return redirect("/login")
        else:
            if response.get("type") == "<class 'sqlalchemy.exc.IntegrityError'>":
                error = "Такой пользователь уже существует"
            else:
                error = response.get("error")
            return render_template("register.html", title=title, form=form,
                                   error_message=error, jwt=get_jwt())
    return render_template("register.html", title=title, form=form, jwt=get_jwt())


@app.route("/login", methods=["GET", "POST"])
@jwt_required(optional=True)
def login():
    if get_jwt():
        return redirect("/")
    title = "Вход"
    form = LoginForm()
    if request.form:
        response = requests.post("http://localhost:5000/api/login", json=dict(request.form)).json()
        if "access_token" in response:
            re = redirect("/")
            set_access_cookies(re, response.get("access_token"))
            set_refresh_cookies(re, response.get("refresh_token"))
            return re
        else:
            return render_template("login.html", title=title, form=form,
                                   error_message=response.get("error"), jwt=get_jwt())
    messages = get_flashed_messages()
    if messages and messages[0] == "Аккаунт создан":
        return render_template("login.html",
                               title=title, form=form, success_message=messages[0], jwt=get_jwt())
    return render_template("login.html", title=title, form=form, jwt=get_jwt())

@app.route("/new_recipe", methods=["GET", "POST"])
@jwt_required(optional=True)
def new_recipe():
    title = "Новый рецепт"
    form = RecipeForm()
    if request.form:
        return dict(request.form)
    return render_template("recipe_edit.html", title=title, jwt=get_jwt(), form=form)


@app.route("/logout")
def logout():
    re = redirect("/")
    unset_jwt_cookies(re)
    return re


def main():
    app.register_blueprint(api.blueprint, url_prefix="/api")
    app.run()


if __name__ == '__main__':
    main()
