from flask_login import UserMixin
from sqlalchemy import Integer, Column, String, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy_serializer import SerializerMixin
from werkzeug.security import generate_password_hash, check_password_hash

from ..db_session import SqlAlchemyBase


class User(SqlAlchemyBase, UserMixin, SerializerMixin):
    __tablename__ = "user"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(30), index=True, unique=True, nullable=False)
    password = Column(String(30), nullable=False)
    about = Column(String(500), nullable=True)
    admin = Column(Boolean, nullable=False)

    recipes = relationship("Recipe", backref="user", cascade="all, delete-orphan")

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)
