import base64
import os
from datetime import timedelta

import requests
from flask import Flask, render_template, request, redirect, flash, get_flashed_messages, abort
from flask_jwt_extended import JWTManager, set_access_cookies, set_refresh_cookies, get_jwt, jwt_required, \
    unset_jwt_cookies, verify_jwt_in_request

import api
from db.db_operations import DatabaseOperations
from forms.login import LoginForm
from forms.recipe import RecipeForm
from forms.register import RegisterForm
from swagger import swagger_ui_blueprint, SWAGGER_URL

db = DatabaseOperations("db.sqlite")

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'my-secret-key')
app.config['UPLOAD_FOLDER'] = 'static/uploads/'

app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY', 'dev-secret-key')
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(days=2)
app.config['JWT_REFRESH_TOKEN_EXPIRES'] = timedelta(days=30)
app.config['JWT_COOKIE_CSRF_PROTECT'] = False
app.config['JWT_TOKEN_LOCATION'] = ['cookies']

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


@jwt.unauthorized_loader
def handle_unauthorized_error(callback):
    return redirect("/login")


@app.errorhandler(403)
def page_not_found(error):
    return render_template('error.html', code="403", text="Доступ запрещен")


@app.errorhandler(404)
def page_not_found(error):
    return render_template('error.html', code="404", text="Страница не найдена")


@app.errorhandler(500)
def page_not_found(error):
    return render_template('error.html', code="500", text="Произошла непредвиденная ошибка на сервере")


@app.route("/", methods=["GET"])
@app.route("/index", methods=["GET"])
def index():
    verify_jwt_in_request(optional=True)
    title = "Главная"
    page = request.args.get("page", 1, type=int)
    response = requests.get(f"http://localhost:5000/api/recipes?page={page}&pages_info=true").json()
    recipes_list = response.get("recipes")
    pages = response.get("pages")
    return render_template("recipe_list.html", title=title, recipes=recipes_list,
                           page=page, pages=pages, jwt=get_jwt())


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
@jwt_required()
def new_recipe():
    title = "Новый рецепт"
    form = RecipeForm()
    if form.validate_on_submit():
        form.main_image.data = base64.b64encode(form.main_image.data.read()).decode('utf-8')
        for part in form.recipe_parts:
            data = part.step_image.data
            if data:
                part.step_image.data = base64.b64encode(data.read()).decode('utf-8')
        response = requests.post("http://localhost:5000/api/recipes", cookies=request.cookies, json=form.data).json()
        print(response)
        if "id" in response:
            return redirect(f"/recipes/{response.get('id')}")
        else:
            abort(500)
    return render_template("recipe_edit.html", title=title, jwt=get_jwt(), form=form)


# @app.route("/recipes/<int:recipe_id>/edit", methods=["GET", "PUT"])
# @jwt_required()
# def edit_recipe(recipe_id):
#     title = "Редактирование рецепта"
#     form = RecipeForm(edit_mode=True)
#     if form.validate_on_submit:
#         print(form.data)
#     recipe_dict = requests.get(f"http://localhost:5000/api/recipes/{recipe_id}").json()
#     if recipe_dict:
#         # user_id = get_jwt_identity()
#         return render_template("recipe_edit.html", title=title, jwt=get_jwt(), form=form,
#                                existing_recipe=recipe_dict)
#     else:
#         abort(404)

@app.route("/recipes/<int:recipe_id>", methods=["GET"])
@jwt_required(optional=True)
def recipe(recipe_id):
    recipe_dict = requests.get(f"http://localhost:5000/api/recipes/{recipe_id}").json()
    if "error" in recipe_dict:
        abort(404)
    return render_template("recipe.html", title=recipe_dict.get("title"),
                           recipe=recipe_dict, jwt=get_jwt())


@app.route("/recipes/<int:recipe_id>/delete")
@jwt_required()
def delete_recipe(recipe_id):
    response = requests.delete(f"http://localhost:5000/api/recipes/{recipe_id}", cookies=request.cookies).json()
    if "success" in response:
        return redirect("/")
    elif "error" in response:
        if response.get("error").startswith("404"):
            abort(404)
        elif response.get("error").startswith("403"):
            abort(403)
        else:
            abort(500)
    else:
        abort(500)


@app.route("/users/<int:user_id>", methods=["GET"])
@jwt_required(optional=True)
def user(user_id):
    page = request.args.get("page", 1, type=int)
    user_dict = requests.get(f"http://localhost:5000/api/users/{user_id}?page={page}").json()
    if "error" in user_dict:
        abort(404)
    response = requests.get(f"http://localhost:5000/api/recipes?user_id={user_id}&page={page}&pages_info=true").json()
    recipes_list = response.get("recipes")
    pages = response.get("pages")
    if recipes_list or page == 1:
        return render_template("profile.html", title=user_dict.get("username"),
                               recipes=recipes_list, user=user_dict, page=page, pages=pages, jwt=get_jwt())
    else:
        abort(404)


@app.route("/search", methods=["GET"])
@jwt_required(optional=True)
def search():
    search_title = request.args.get("title", None)
    search_tags = request.args.get("tags", None)
    page = request.args.get("page", 1, type=int)
    response = requests.get(f"http://localhost:5000/api/recipes"
                            f"?page={page}"
                            f"{('&title=' + search_title.strip()) if search_title else ''}"
                            f"{('&tags=' + search_tags.strip()) if search_tags else ''}"
                            f"&pages_info=true").json()
    recipes_list = response.get("recipes")
    pages = response.get("pages")
    if recipes_list or page == 1:
        return render_template("search.html", title=search_title, recipes=recipes_list,
                               page=page, pages=pages, jwt=get_jwt())
    else:
        abort(404)


@app.route("/logout")
def logout():
    re = redirect("/")
    unset_jwt_cookies(re)
    return re


def main():
    app.register_blueprint(api.blueprint, url_prefix="/api", config=app.config)
    app.register_blueprint(swagger_ui_blueprint, url_prefix=SWAGGER_URL)
    app.run()


if __name__ == '__main__':
    main()
