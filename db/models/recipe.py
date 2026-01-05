import datetime

from sqlalchemy import Column, Integer, String, Float, Enum, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from enum import Enum as PyEnum

from sqlalchemy_serializer import SerializerMixin
from ..db_session import SqlAlchemyBase


class Unit(PyEnum):
    GRAM = "г"
    KILOGRAM = "кг"
    LITER = "л"
    MILLILITER = "мл"
    PIECE = "шт."
    TABLESPOON = "ст. л."
    TEASPOON = "ч. л."
    CUP = "стакан"


class Ingredient(SqlAlchemyBase, SerializerMixin):
    __tablename__ = "ingredient"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    amount = Column(Float, nullable=False)
    unit = Column(Enum(Unit), nullable=False)
    recipe_id = Column(Integer, ForeignKey("recipe.id"))


class RecipePart(SqlAlchemyBase, SerializerMixin):
    __tablename__ = "recipe_part"
    id = Column(Integer, primary_key=True, autoincrement=True)
    image = Column(String, nullable=True)
    text = Column(String(500), nullable=False)
    recipe_id = Column(Integer, ForeignKey("recipe.id"))


class Recipe(SqlAlchemyBase, SerializerMixin):
    __tablename__ = "recipe"
    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(100), nullable=False)
    description = Column(String(500), nullable=False)
    tags = Column(String(100), nullable=True)
    image = Column(String, nullable=True)
    created_date = Column(DateTime, default=datetime.datetime.now)
    user_id = Column(Integer, ForeignKey("user.id"))

    ingredients = relationship("Ingredient", backref="recipe", cascade="all, delete-orphan")
    recipe_parts = relationship("RecipePart", backref="recipe", cascade="all, delete-orphan")