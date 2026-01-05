from typing import Optional, List

from db.db_session import global_init, create_session
from db.models.recipe import Recipe, Ingredient, RecipePart
from db.models.user import User


class DatabaseOperations:
    def __init__(self, db_file: str):
        global_init(db_file)

    def create_user(self, username: str, password: str, about: str = None, admin: bool = False):
        with create_session() as session:
            user = User(username=username,
                        about=about,
                        admin=admin)
            user.set_password(password)
            session.add(user)
            session.commit()
            session.refresh(user)

    def get_user_by_id(self, user_id: int) -> Optional[User]:
        with create_session() as session:
            user = session.query(User).filter(User.id == user_id).first()
            return user

    def get_user_by_username(self, username: str) -> Optional[User]:
        with create_session() as session:
            user = session.query(User).filter(User.username == username).first()
            return user

    def update_user(self, user_id: int, **kwargs):
        with create_session() as session:
            user = session.query(User).filter(User.id == user_id).first()
            if user:
                for key, value in kwargs.items():
                    if hasattr(user, key):
                        if key != "password":
                            setattr(user, key, value)
                        else:
                            user.set_password(value)
                session.commit()
                session.refresh(user)

    def create_recipe(self, title: str, description: str, user_id: int,
                      tags: str = None, image: str = None,
                      ingredients: list = None, recipe_parts: list = None):
        with create_session() as session:
            recipe = Recipe(
                title=title,
                description=description,
                tags=tags,
                image=image,
                user_id=user_id)

            if ingredients:
                for ing in ingredients:
                    ingredient = Ingredient(
                        name=ing['name'],
                        amount=ing['amount'],
                        unit=ing['unit'])
                    recipe.ingredients.append(ingredient)

            if recipe_parts:
                for part in recipe_parts:
                    recipe_part = RecipePart(
                        image=part.get('image'),
                        text=part['text']
                    )
                    recipe.recipe_parts.append(recipe_part)

            session.add(recipe)
            session.commit()
            session.refresh(recipe)

    def update_recipe(self, recipe_id: int, **kwargs):
        with create_session() as session:
            recipe = session.query(Recipe).filter(Recipe.id == recipe_id).first()
            if recipe:

                for key, value in kwargs.items():
                    if hasattr(recipe, key) and key not in ['ingredients', 'recipe_parts']:
                        setattr(recipe, key, value)

                if 'ingredients' in kwargs:
                    for ingredient in recipe.ingredients[:]:
                        session.delete(ingredient)
                    recipe.ingredients.clear()
                    for ing in kwargs['ingredients']:
                        ingredient = Ingredient(
                            name=ing['name'],
                            amount=ing['amount'],
                            unit=ing['unit']
                        )
                        recipe.ingredients.append(ingredient)

                if 'recipe_parts' in kwargs:
                    for part in recipe.recipe_parts[:]:
                        session.delete(part)
                    recipe.recipe_parts.clear()
                    for part in kwargs['recipe_parts']:
                        recipe_part = RecipePart(
                            image=part.get('image'),
                            text=part['text']
                        )
                        recipe.recipe_parts.append(recipe_part)

                session.commit()
                session.refresh(recipe)

    def get_recipe_by_id(self, recipe_id: int) -> Optional[Recipe]:
        with create_session() as session:
            recipe = session.query(Recipe).filter(Recipe.id == recipe_id).first()
            return recipe

    def get_recipes(self, tags: str = None, title: str = None, page: int = 1) -> List[Recipe]:
        with create_session() as session:
            query = session.query(Recipe)

            if title:
                query = query.filter(Recipe.title.ilike(f"%{title}%"))

            if tags:
                tag_list = [tag.strip() for tag in tags.split(',')]
                for tag in tag_list:
                    query = query.filter(Recipe.tags.ilike(f"%{tag}%"))

            query = query.order_by(Recipe.created_date.desc())

            offset = (page - 1) * 10
            recipes = query.offset(offset).limit(10).all()

            return recipes

    def delete_recipe(self, recipe_id: int):
        with create_session() as session:
            recipe = session.query(Recipe).filter(Recipe.id == recipe_id).first()
            if recipe:
                session.delete(recipe)
                session.commit()
