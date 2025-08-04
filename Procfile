web: gunicorn --worker-tmp-dir /dev/shm --bind 0.0.0.0:$PORT --timeout 120 --graceful-timeout 120 shop.wsgi:application
