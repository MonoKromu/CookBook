import jwt.exceptions
import sqlalchemy.exc
from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, create_refresh_token, jwt_required, get_jwt

from db.db_operations import DatabaseOperations

blueprint = Blueprint('api', __name__, template_folder='templates')
db = DatabaseOperations("db.sqlite")


@blueprint.errorhandler(sqlalchemy.exc.SQLAlchemyError)
def handle_db_error(error):
    print(error, type(error))
    return jsonify({"error": "Bad Request", "type": str(type(error))}), 400


@blueprint.errorhandler(jwt.exceptions.ExpiredSignatureError)
def handle_expired_error(error):
    return jsonify({"error": "Expired Signature"}), 401


@blueprint.errorhandler(Exception)
def handle_error(error):
    print(error, type(error))
    return jsonify({"error": "Internal Server Error", "type": str(type(error))}), 500


@blueprint.route("/login", methods=["POST"])
def login():
    if request.is_json:
        data = request.get_json()
    else:
        return jsonify({"error": "Unsupported Media Type"}), 415
    username = data.get('username')
    password = data.get('password')
    user = db.get_user_by_username(username)
    if user and user.check_password(password):
        additional_claims = {"username": user.username, "admin": user.admin}
        access_token = create_access_token(identity=str(user.id), additional_claims=additional_claims, fresh=True)
        refresh_token = create_refresh_token(identity=str(user.id), additional_claims=additional_claims)
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
    db.create_user(username, password, about)
    return jsonify({"success": "OK"})


@blueprint.route("/refresh")
@jwt_required(refresh=True)
def refresh():
    jwt = get_jwt()
    additional_claims = {"username": jwt.get("username"), "admin": jwt.get("admin")}
    new_token = create_access_token(identity=jwt.get("sub"), additional_claims=additional_claims)
    return jsonify({"access_token": new_token})
