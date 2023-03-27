# Foodgram - «Продуктовый помощник»

## Описание проекта Foodgram
«Продуктовый помощник»: приложение, на котором пользователи публикуют рецепты кулинарных изделий, подписываться на публикации других авторов и добавлять рецепты в свое избранное.
Сервис «Список покупок» позволит пользователю создавать список продуктов, которые нужно купить для приготовления выбранных блюд согласно рецепта/ов.

Проект доступен по ссыле - http://158.160.47.208/
```
Данные админа:
email: admin@admin.ru
password: admin
```

## Технологический стек
Python
Django
Django REST Framework
PostgreSQL
JWT
Nginx
Docker

## Запуск проекта
Клонируйте репозиторий и перейдите в него в командной строке:
```
git clone ...
```
Создайте и активируйте виртуальное окружение, обновите pip:
```
python3 -m venv venv
. venv/bin/activate
python3 -m pip install --upgrade pip
```

Перенести файлы docker-compose.yml и nginx.conf на сервер, из папки infra в текущем репозитории.

```
cd infra
```

```
scp docker-compose.yml username@server_ip:/home/username/
```

```
scp default.conf username@server_ip:/home/username/
```

Так же, создаем файл .env на ВМ:

```
touch .env
```

Заполнить в настройках репозитория секреты .env

```
DB_ENGINE='django.db.backends.postgresql'
DB_NAME=postgres # имя базы данных
POSTGRES_USER=postgres # логин для подключения к базе данных
POSTGRES_PASSWORD=postgres # пароль для подключения к БД (установите свой)
DB_HOST=db # название сервиса (контейнера)
DB_PORT=5432 # порт для подключения к БД
ALLOWED_HOSTS=localhost, 127.0.0.1
SECRET_KEY=svoy_secret
```


Для доступа к контейнеру backend и сборки выполняем следующие команды:

```
sudo docker-compose exec backend python manage.py makemigrations
```

```
sudo docker-compose exec backend python manage.py migrate --noinput
```

```
sudo docker-compose exec backend python manage.py createsuperuser
```

```
sudo docker-compose exec backend python manage.py collectstatic --no-input
```

Дополнительно можно наполнить DB ингредиентами и тэгами:

```
sudo docker-compose exec backend python manage.py load_tags
```

```
sudo docker-compose exec backend python manage.py load_ingredients
```

Продуктовый помощник запущен.
