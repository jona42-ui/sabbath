web: gunicorn wsgi:app --log-file -
worker: celery -A app.tasks worker --loglevel=info