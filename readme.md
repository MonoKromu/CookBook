# CookBook
Сайт для публикации и просмотра различных рецептов
## Возможности:
- Аутентификация пользователей
- Публикация рецептов со списком ингредиентов, пошаговым описанием и прикрепляемыми картинками
- Просмотр всех рецептов на главной странице
- Профили пользователей со списком их рецептов
- Поиск по названию и тегам

## Используемые технологии:
- Flask для создания веб приложения
- Jinja2 для шаблонизации html-страниц
- Flask-wtf для работы с формами
- SqlAlchemy - работа с базой данных sqlite
- Swagger - документация к api


## Запуск веб сервера (Windows, python 3.12)
Открыть консоль в папке с проектом. Создать и активировать виртуальное окружение.

    python -m venv folder_name
    cd folder_name
    Scripts\activate
Установить необходимые пакеты:

    pip install -r requirements.txt
Запустить сервер:

    python main.py
При необходимости можно поменять адрес и порт, на котором запускается сервер.
Документация по api по адресу /docs.

## Демонстрация работы
![Страница с рецептом](https://raw.githubusercontent.com/monokromu/cookbook/master/demo/1.png)
![Страница создания рецепта](https://raw.githubusercontent.com/monokromu/cookbook/master/demo/2.png)
![Страница поиска](https://raw.githubusercontent.com/monokromu/cookbook/master/demo/3.png)
![Регистрация пользователя](https://raw.githubusercontent.com/monokromu/cookbook/master/demo/4.png)