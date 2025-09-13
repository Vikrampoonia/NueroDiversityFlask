FROM python:3.10-slim


WORKDIR /app


COPY requirements.txt .


RUN pip install --no-cache-dir -r requirements.txt


COPY . .


CMD gunicorn --bind 0.0.0.0:5000 api_gateway:app & celery -A celery_worker.celery_app worker --loglevel=info