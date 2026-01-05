from flask import Flask, request, render_template
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, FloatField, SelectField, FieldList, FormField, SubmitField
from wtforms.validators import DataRequired, Length, Optional, NumberRange
from flask_wtf.file import FileField, FileAllowed, FileRequired
from enum import Enum

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key'

class Unit(Enum):
    GRAM = "г"
    KILOGRAM = "кг"
    LITER = "л"
    MILLILITER = "мл"
    PIECE = "шт."
    TABLESPOON = "ст. л."
    TEASPOON = "ч. л."
    CUP = "стакан"

class IngredientForm(FlaskForm):
    name = StringField(
        'Название ингредиента',
        validators=[DataRequired(message="Введите название ингредиента"),
                    Length(max=100)]
    )
    amount = FloatField(
        'Количество',
        validators=[
            DataRequired(message="Введите количество"),
            NumberRange(min=0.01, message="Количество должно быть больше 0")
        ]
    )
    unit = SelectField(
        'Единица измерения',
        choices=[(unit.name, unit.value) for unit in Unit],
        validators=[DataRequired(message="Выберите единицу измерения")]
    )

class RecipePartForm(FlaskForm):
    text = TextAreaField(
        'Описание шага',
        validators=[
            DataRequired(message="Введите описание шага"),
            Length(max=500, message="Описание не должно превышать 500 символов")
        ]
    )
    step_image = FileField(
        'Изображение для шага',
        validators=[
            Optional(),
            FileAllowed(['jpg', 'jpeg', 'png', 'gif'], 'Только изображения!')
        ]
    )

class RecipeForm(FlaskForm):
    title = StringField(
        'Название рецепта',
        validators=[
            DataRequired(message="Введите название рецепта"),
            Length(max=100, message="Название не должно превышать 100 символов")
        ]
    )

    description = TextAreaField(
        'Описание рецепта',
        validators=[
            DataRequired(message="Введите описание рецепта"),
            Length(max=500, message="Описание не должно превышать 500 символов")
        ]
    )

    tags = StringField(
        'Теги (через запятую)',
        validators=[
            Optional(),
            Length(max=100, message="Теги не должны превышать 100 символов")
        ],
        description="Например: десерт, выпечка, вегетарианское"
    )

    main_image = FileField(
        'Главное изображение рецепта',
        validators=[
            FileRequired(message="Загрузите главное изображение"),
            FileAllowed(['jpg', 'jpeg', 'png', 'gif'], 'Только изображения!')
        ]
    )

    ingredients = FieldList(
        FormField(IngredientForm),
        min_entries=1,
        label='Ингредиенты'
    )

    recipe_parts = FieldList(
        FormField(RecipePartForm),
        min_entries=1,
        label='Шаги приготовления'
    )

    submit = SubmitField('Сохранить рецепт')