FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .

RUN apt-get update && apt-get upgrade -y && \
    pip install --upgrade pip && pip install -r /app/foodgram/requirements.txt

COPY ./ ./

CMD ["gunicorn", "foodgram.wsgi:application", "--bind", "0.0.0.0:8000"]