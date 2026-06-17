#!/bin/sh

python manage.py migrate --noinput

python manage.py collectstatic --noinput

gunicorn kittygram.wsgi:application --bind 0.0.0.0:8000