release: python manage.py migrate && python manage.py collectstatic --noinput
web: gunicorn shop.wsgi:application --bind 0.0.0.0:$PORT --timeout 120 --graceful-timeout 120 --worker-tmp-dir /dev/shm