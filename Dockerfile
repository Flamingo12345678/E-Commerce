FROM python:3.11-slim

# Variables d'environnement
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DEBIAN_FRONTEND=noninteractive

# Répertoire de travail
WORKDIR /opt/app

# Installation des dépendances système
RUN apt-get update && apt-get install -y \
    gcc \
    default-libmysqlclient-dev \
    pkg-config \
    postgresql-client \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Installation des dépendances Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir psycopg2-binary gunicorn

# Copie du code
COPY . .

# Création des répertoires nécessaires
RUN mkdir -p /opt/app/staticfiles /opt/app/media

# Configuration des permissions pour App Platform
RUN useradd --create-home --shell /bin/bash app \
    && chown -R app:app /opt/app
USER app

# Collecte des fichiers statiques (avec variables d'environnement par défaut)
ENV DEBUG=False
ENV SECRET_KEY=temp-key-for-collectstatic
ENV ALLOWED_HOSTS=localhost
RUN python manage.py collectstatic --noinput

# Exposition du port
EXPOSE 8000

# Commande de démarrage optimisée pour App Platform
CMD ["gunicorn", "--worker-tmp-dir", "/dev/shm", "--workers", "2", "--bind", "0.0.0.0:8000", "--max-requests", "1000", "--timeout", "30", "shop.wsgi:application"]
