FROM python:3.8

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN apk update \
    && pip install --upgrade pip \
    && apk add --virtual build-deps gcc python3-dev musl-dev
    && apk add libpq \
    && apk add postgresql-dev \
    && apk add jpeg-dev zlib-dev libjpeg \
    && apk del build-deps

WORKDIR /app

COPY requirements.txt .

RUN pip3 install -r requirements.txt --no-cache-dir

COPY . .

CMD ["gunicorn", "foodgram.wsgi:application", "--bind", "0.0.0.0:8000"]