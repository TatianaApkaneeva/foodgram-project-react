FROM python:3.8

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN apt update \
    && pip install --upgrade pip \
    && apt add --virtual build-deps gcc python3-dev musl-dev \
    && apt add libpq \
    && apt add postgresql-dev \
    && apt add jpeg-dev zlib-dev libjpeg \
    && apt del build-deps

WORKDIR /app

COPY requirements.txt .

RUN pip3 install -r requirements.txt --no-cache-dir

COPY . .

CMD ["gunicorn", "foodgram.wsgi:application", "--bind", "0.0.0.0:8000"]