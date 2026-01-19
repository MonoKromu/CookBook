from db.db_session import global_init, create_session
from db.models.recipe import Recipe, Ingredient, RecipePart
from db.models.user import User


class DatabaseOperations:
    def __init__(self, db_file: str):
        global_init(db_file)

    def check_user_password(self, username: str, password: str):
        with create_session() as session:
            user = session.query(User).filter(User.username == username).first()
            if user and user.check_password(password):
                return True
            else:
                return False

    def create_user(self, username: str, password: str, about: str = None, admin: bool = False):
        with create_session() as session:
            user = User(username=username,
                        about=about,
                        admin=admin)
            user.set_password(password)
            session.add(user)
            session.commit()
            session.refresh(user)
            return user.id

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
                return user.id
            return None

    def get_user_by_id(self, user_id: int):
        with create_session() as session:
            user = session.query(User).filter(User.id == user_id).first()
            serialized_values = ["id", "username", "about", "admin"]
            return user.to_dict(only=serialized_values) if user else None

    def get_user_by_username(self, username: str):
        with create_session() as session:
            user = session.query(User).filter(User.username == username).first()
            serialized_values = ["id", "username", "about", "admin"]
            return user.to_dict(only=serialized_values) if user else None

    def get_users(self, page: int = 1):
        with create_session() as session:
            query = session.query(User)
            total_pages = (query.count() + 9) // 10
            offset = (page - 1) * 10
            users = query.offset(offset).limit(10).all()

            serialized_fields = ["id", "username", "about", "admin"]
            return [u.to_dict(only=serialized_fields) for u in users], total_pages

    def create_recipe(self, title: str, description: str, user_id: int,
                      tags: str = None, image: str = None,
                      ingredients: list = None, recipe_parts: list = None):
        with create_session() as session:
            recipe = Recipe(
                title=title,
                description=description,
                tags=tags,
                image=image,
                user_id=user_id
            )

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
            return recipe.id

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
                return recipe.id
            return None

    def get_recipe_by_id(self, recipe_id: int):
        with create_session() as session:
            recipe = session.query(Recipe).filter(Recipe.id == recipe_id).first()
            serialized_fields = ["id", "title", "description", "tags", "created_date", "image",
                                 "user.id", "user.username",
                                 "ingredients.name", "ingredients.amount", "ingredients.unit",
                                 "recipe_parts.text", "recipe_parts.image"]
            return recipe.to_dict(max_serialization_depth=1, only=serialized_fields) if recipe else None

    def get_recipes(self, tags: str = None, title: str = None, user_id: int = None, page: int = 1):
        with create_session() as session:
            query = session.query(Recipe)
            if user_id:
                query = query.filter(Recipe.user_id == user_id)
            if title:
                query = query.filter(Recipe.title.ilike(f"%{title}%"))
            if tags:
                tag_list = [tag.strip() for tag in tags.split(',')]
                for tag in tag_list:
                    query = query.filter(Recipe.tags.ilike(f"%{tag}%"))

            total_pages = (query.count() + 9) // 10

            query = query.order_by(Recipe.created_date.desc())
            offset = (page - 1) * 10
            recipes = query.offset(offset).limit(10).all()

            serialized_fields = ["id", "title", "description", "tags", "created_date", "image",
                                 "user.id", "user.username"]
            return [r.to_dict(max_serialization_depth=1, only=serialized_fields) for r in recipes], total_pages

    def delete_recipe(self, recipe_id: int):
        with create_session() as session:
            recipe = session.query(Recipe).filter(Recipe.id == recipe_id).first()
            if recipe:
                session.delete(recipe)
                session.commit()
                return recipe
            return None
