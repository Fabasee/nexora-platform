# Nexora API

Django REST Framework service. The first endpoint is `GET /api/v1/health/`.

## Local setup

```bash
python -m venv .venv
# Activate the virtual environment, then:
pip install -r requirements.txt
cp .env.example .env
python manage.py check
python manage.py migrate
python manage.py runserver
```

Never place Firebase Admin credentials in this directory or commit a populated `.env`.
