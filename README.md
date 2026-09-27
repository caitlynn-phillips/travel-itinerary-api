# Travel Itinerary Planning & Booking API

A Django REST Framework API for browsing destinations, planning day-by-day
itineraries, booking accommodations/activities, tracking budgets, and
collaborating with travel companions.

## Technologies

Django 6.1, Django REST Framework, Simple JWT, django-filter, drf-spectacular,
Pillow, SQLite (dev) / PostgreSQL (prod), pytest-django.

## Setup

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env            # then fill in SECRET_KEY etc.
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

## Environment variables (`.env`)

See `.env.example` — `SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS`, and optional
`USE_POSTGRES`/`DB_*` vars to switch off the default SQLite database.

## Running tests

```bash
pytest                 # or: python manage.py test
pytest --cov=.         # with coverage report
```

## API documentation

Once the server is running:
- Swagger UI: `http://localhost:8000/api/docs/`
- ReDoc: `http://localhost:8000/api/redoc/`
- Raw schema: `http://localhost:8000/api/schema/`

## Project structure

See `docs/planning.md` for the full ERD, endpoint list, auth flow, and
permission matrix. Apps: `accounts`, `destinations`, `itineraries`,
`bookings`, `reviews`, `budgets` — each with its own `models.py`,
`serializers.py`, `views.py`, `urls.py`, and `tests.py`.

## Status

🚧 Scaffold stage: project structure, settings, custom `User` model, and
routing are in place. Models, serializers, views, permissions, filters, and
tests for each app are being built out next.
