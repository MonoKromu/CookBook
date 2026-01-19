import base64
import uuid
from io import BytesIO

import jwt.exceptions
import sqlalchemy.exc
from PIL import Image
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import create_access_token, create_refresh_token, jwt_required, get_jwt, get_jwt_identity

from db.db_operations import DatabaseOperations

blueprint = Blueprint('api', __name__, template_folder='templates')
db = DatabaseOperations("db.sqlite")


@blueprint.errorhandler(sqlalchemy.exc.SQLAlchemyError)
def handle_db_error(error):
    print(error, type(error))
    return jsonify({"error": "Bad Request", "type": str(type(error))}), 400


@blueprint.errorhandler(jwt.exceptions.ExpiredSignatureError)
def handle_expired_error(error):
    print(error, type(error))
    return jsonify({"error": "Expired Signature"}), 401


@blueprint.errorhandler(Exception)
def handle_error(error: Exception):
    print(error, type(error))
    return jsonify({"error": "Internal Server Error" if not str(error) else str(error), "type": str(type(error))}), 500


@blueprint.route("/login", methods=["POST"])
def login():
    if request.is_json:
        data = request.get_json()
    else:
        return jsonify({"error": "Unsupported Media Type"}), 415
    username = data.get('username')
    password = data.get('password')
    user = db.get_user_by_username(username)
    if db.check_user_password(username, password):
        additional_claims = {"username": username, "admin": user.get("admin")}
        access_token = create_access_token(identity=str(user.get("id")), additional_claims=additional_claims,
                                           fresh=True)
        refresh_token = create_refresh_token(identity=str(user.get("id")), additional_claims=additional_claims)
        return jsonify({
            "access_token": access_token,
            "refresh_token": refresh_token,
        })
    else:
        return jsonify({"error": "Wrong login or password"}), 401


@blueprint.route("/register", methods=["POST"])
def register():
    if request.is_json:
        data = request.get_json()
    else:
        return jsonify({"error": "Unsupported Media Type"}), 415
    username = data.get("username")
    password = data.get("password")
    about = data.get("about")
    user_id = db.create_user(username, password, about)
    return jsonify({"success": "OK", "id": user_id})


@blueprint.route("/recipes", methods=["POST"])
@jwt_required()
def create_recipe():
    if request.is_json:
        data = request.get_json()
    else:
        return jsonify({"error": "Unsupported Media Type"}), 415
    main_image = convert_to_image(data.get("main_image"))
    main_image_filename = f"{current_app.config['UPLOAD_FOLDER']}{uuid.uuid4()}.jpg"
    main_image.save(main_image_filename)

    ingredients_list = []
    for ingredient in data.get("ingredients"):
        ingredients_list.append({
            "name": ingredient.get("name"),
            "amount": ingredient.get("amount"),
            "unit": ingredient.get("unit")
        })
    recipe_parts_list = []
    for part in data.get("recipe_parts"):
        step_image_filename = None
        if part.get("step_image"):
            step_image = convert_to_image(part.get("step_image"))
            step_image_filename = f"{current_app.config['UPLOAD_FOLDER']}{uuid.uuid4()}.jpg"
            step_image.save(step_image_filename)

        recipe_parts_list.append({
            "text": part.get("text"),
            "image": step_image_filename
        })

    user_id = get_jwt_identity()
    recipe_id = db.create_recipe(
        title=data.get("title"),
        description=data.get("description"),
        user_id=user_id,
        tags=data.get("tags"),
        image=main_image_filename,
        ingredients=ingredients_list,
        recipe_parts=recipe_parts_list
    )
    return jsonify({"success": "OK", "id": recipe_id})


# @blueprint.route("/recipes/<int:recipe_id>", methods=["PUT"])
# @jwt_required()
# def update_recipe():
#     if request.is_json:
#         data = request.get_json()
#     else:
#         return jsonify({"error": "Unsupported Media Type"}), 415
#
#     edited_recipe = db.get_recipe_by_id(data.get("id"))
#     if not edited_recipe:
#         return jsonify({"error": "404 Not Found"})
#     if get_jwt_identity() != edited_recipe.get("user").get("id"):
#         return jsonify({"error": "403 Forbidden"})
#
#     if data.get("main_image"):
#         main_image = convert_to_image(data.get("main_image"))
#         main_image_filename = f"{current_app.config['UPLOAD_FOLDER']}{uuid.uuid4()}.jpg"
#         main_image.save(main_image_filename)
#     else:
#         main_image_filename = data.get("image")
#
#     ingredients_list = []
#     for ingredient in data.get("ingredients"):
#         ingredients_list.append({
#             "name": ingredient.get("name"),
#             "amount": ingredient.get("amount"),
#             "unit": ingredient.get("unit")
#         })
#     recipe_parts_list = []
#     for i, part in enumerate(data.get("recipe_parts")):
#         step_image_filename = None
#         if part.get("step_image"):
#             step_image = convert_to_image(part.get("step_image"))
#             step_image_filename = f"{current_app.config['UPLOAD_FOLDER']}{uuid.uuid4()}.jpg"
#             step_image.save(step_image_filename)
#         elif data.get("ingredients")[i]
#
#         recipe_parts_list.append({
#             "text": part.get("text"),
#             "image": step_image_filename
#         })
#
#     user_id = get_jwt_identity()
#     recipe_id = db.create_recipe(
#         title=data.get("title"),
#         description=data.get("description"),
#         user_id=user_id,
#         tags=data.get("tags"),
#         image=main_image_filename,
#         ingredients=ingredients_list,
#         recipe_parts=recipe_parts_list
#     )
#     return jsonify({"success": "OK", "id": recipe_id})


@blueprint.route("/recipes", methods=["GET"])
def get_recipes():
    tags = request.args.get("tags", None)
    title = request.args.get("title", None)
    user_id = request.args.get("user_id", None)
    page = request.args.get("page", 1, type=int)
    recipes, pages = db.get_recipes(tags=tags, title=title, user_id=user_id, page=page)
    if not recipes:
        recipes = []

    response = {"recipes": recipes}
    if request.args.get("pages_info", None):
        response["pages"] = pages
    return jsonify(response)


@blueprint.route("/recipes/<int:recipe_id>", methods=["DELETE"])
@jwt_required()
def delete_recipe(recipe_id):
    recipe = db.get_recipe_by_id(recipe_id)
    if not recipe:
        return jsonify({"error": "404 Not Found"})
    elif int(get_jwt_identity()) != recipe.get("user").get("id"):
        return jsonify({"error": "403 Forbidden"})
    else:
        db.delete_recipe(recipe_id)
        return jsonify({"success": "OK", "id": recipe_id})


@blueprint.route("/recipes/<int:recipe_id>", methods=["GET"])
def get_recipe(recipe_id):
    recipe = db.get_recipe_by_id(recipe_id=recipe_id)
    return recipe if recipe else jsonify({"error": "404 Not Found"})


@blueprint.route("/users", methods=["GET"])
def get_users():
    page = request.args.get("page", 1, type=int)
    users, pages = db.get_users(page=page)
    if not users:
        users = []
    response = {"users": users}

    if request.args.get("pages_info", None):
        response["pages"] = pages
    return jsonify(response)


@blueprint.route("/users/<int:user_id>", methods=["GET"])
def get_user(user_id):
    user = db.get_user_by_id(user_id=user_id)
    return user if user else jsonify({"error": "404 Not Found"})


def convert_to_image(b64text):
    try:
        image_data = base64.b64decode(b64text)
        img = Image.open(BytesIO(image_data))
        img.verify()
        img = Image.open(BytesIO(image_data))
        return img
    except Exception as _:
        raise Exception("Invalid Image File")


@blueprint.route("/refresh")
@jwt_required(refresh=True)
def refresh():
    token = get_jwt()
    additional_claims = {"username": token.get("username"), "admin": token.get("admin")}
    new_token = create_access_token(identity=token.get("sub"), additional_claims=additional_claims)
    return jsonify({"access_token": new_token})
