from enum import Enum

from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed, FileRequired
from wtforms import StringField, TextAreaField, SelectField, FieldList, FormField, SubmitField, Form
from wtforms.fields.numeric import IntegerField
from wtforms.validators import DataRequired, Length, Optional, NumberRange


class Unit(Enum):
    GRAM = "г"
    KILOGRAM = "кг"
    LITER = "л"
    MILLILITER = "мл"
    PIECE = "шт."
    TABLESPOON = "ст. л."
    TEASPOON = "ч. л."
    CUP = "стакан"


class IngredientForm(Form):
    name = StringField(
        'Название',
        validators=[DataRequired(message="Введите название ингредиента"),
                    Length(max=100)]
    )
    amount = IntegerField(
        'Количество',
        validators=[
            DataRequired(message="Введите количество"),
            NumberRange(min=1, message="Количество должно быть больше 0")
        ],
        default=100,
        render_kw={"type": "number", "step": "1"}
    )
    unit = SelectField(
        'Единица измерения',
        choices=[(unit.name, unit.value) for unit in Unit],
        validators=[DataRequired(message="Выберите единицу измерения")]
    )

    class Meta:
        csrf = False


class RecipePartForm(Form):
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

    class Meta:
        csrf = False


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
        label='Ингредиенты',
    )

    recipe_parts = FieldList(
        FormField(RecipePartForm),
        min_entries=1,
        label='Шаги приготовления'
    )

    submit = SubmitField('Сохранить рецепт')

    def __init__(self, *args, edit_mode=False, **kwargs):
        super().__init__(*args, **kwargs)
        if edit_mode:
            self.main_image.validators = [
                FileAllowed(['jpg', 'jpeg', 'png', 'gif'], 'Только изображения!'),
                Optional()
            ]
        else:
            self.main_image.validators = [
                DataRequired(message="Изображение обязательно"),
                FileAllowed(['jpg', 'jpeg', 'png', 'gif'], 'Только изображения!')
            ]
