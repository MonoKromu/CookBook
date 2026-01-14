from flask_wtf import FlaskForm
from wtforms import PasswordField, StringField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, Length, EqualTo


class RegisterForm(FlaskForm):
    username = StringField(
        "Имя пользователя",
        validators=[
            DataRequired(message="Это поле обязательно для заполнения"),
            Length(min=3, max=30, message="Имя пользователя должно быть от 3 до 50 символов")
        ]
    )
    password = PasswordField(
        "Пароль",
        validators=[
            DataRequired(message="Это поле обязательно для заполнения"),
            Length(min=7, max=30, message="Пароль должен содержать от 7 до 30 символов")
        ],
        render_kw={"autocomplete": "new-password"}
    )
    password_again = PasswordField(
        "Повторите пароль",
        validators=[
            EqualTo('password', message="Пароли должны совпадать")
        ],
        render_kw={"autocomplete": "new-password"}
    )
    about = TextAreaField(
        "Информация о вас",
        validators=[
            Length(max=500, message="Описание не более 500 символов")
        ]
    )
    submit = SubmitField("Зарегистрироваться")