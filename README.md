# Travel Itinerary Planning & Booking API

A Django REST Framework API for browsing destinations, planning day-by-day
itineraries, booking accommodations and activities, tracking budgets, and
collaborating with travel companions.

## Technologies

Django 6.1, Django REST Framework, Simple JWT, django-filter, drf-spectacular,
Pillow, SQLite (default) / PostgreSQL (optional), pytest-django, pytest-cov.

## Installation

    python -m venv venv
    source venv/bin/activate        # Windows (Git Bash): source venv/Scripts/activate
    pip install -r requirements.txt
    cp .env.example .env

## Environment variables

Edit `.env` (never commit it):

- `SECRET_KEY`: generate one with
  `python -c "from django.core.management.utils import get_random_secret_key as k; print(k())"`
- `DEBUG`: `True` for local development
- `ALLOWED_HOSTS`: comma-separated hosts, e.g. `localhost,127.0.0.1`
- `USE_POSTGRES`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`:
  only needed for PostgreSQL

## Database setup

SQLite is the default and needs no setup. To use PostgreSQL, uncomment
`psycopg2-binary` in `requirements.txt`, install it, and set
`USE_POSTGRES=True` plus the `DB_*` values in `.env`.

Apply migrations and create an admin user:

    python manage.py migrate
    python manage.py createsuperuser

## Running the server

    python manage.py runserver

## Running tests

    pytest
    pytest --cov=.        # with coverage report

The suite has 41 tests covering models, serializers, views, permissions, and
authentication.

## API documentation

With the server running:

- Swagger UI: http://localhost:8000/api/docs/
- ReDoc: http://localhost:8000/api/redoc/
- Raw schema: http://localhost:8000/api/schema/

## Authentication flow

1. Register or log in. The response includes `access` and `refresh` tokens.
2. Send the access token with every request:
   `Authorization: Bearer <access>`.
3. Access tokens expire after 1 hour. POST your refresh token to
   `/api/v1/accounts/token/refresh/` to get a new one (refresh tokens last
   7 days).

## Example requests

Register (note the password confirmation field):

    curl -X POST http://localhost:8000/api/v1/accounts/register/ \
      -H "Content-Type: application/json" \
      -d '{"username":"demo","email":"demo@example.com","password":"Password123!","password2":"Password123!"}'

Log in:

    curl -X POST http://localhost:8000/api/v1/accounts/login/ \
      -H "Content-Type: application/json" \
      -d '{"username":"demo","password":"Password123!"}'

Fetch your profile (paste the `access` token from the login response):

    curl http://localhost:8000/api/v1/accounts/profile/ \
      -H "Authorization: Bearer <access>"

## Endpoints

All paths start with `/api/v1/`. The full list, with request bodies, is in
Swagger.

- Accounts: `POST accounts/register/`, `accounts/login/`,
  `accounts/token/refresh/`, `accounts/password/change/`,
  `accounts/password/reset/`, `accounts/password/reset/confirm/`;
  `GET/PUT accounts/profile/`
- Resources: `itineraries/`, `destinations/`, `accommodations/`,
  `activities/`, `bookings/`, `reviews/`, `budgets/`, `expenses/`,
  `analytics/`
- Custom: `GET/POST itineraries/search/`, `GET/POST destinations/search-advanced/`,
  `POST bookings/bulk-update/`, `POST reviews/{id}/helpful/`

## Project structure

See `docs/planning.md` for the ERD, endpoint list, auth flow, and permission
matrix. Apps: `accounts`, `destinations`, `itineraries`, `bookings`,
`reviews`, `budgets`, each with its own `models.py`, `serializers.py`,
`views.py`, `urls.py`, and `tests.py`. Project settings, routing, and
pagination live in `travel_api/`.
