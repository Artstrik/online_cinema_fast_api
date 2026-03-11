# Online Cinema FastAPI

Production-oriented backend for an online cinema platform built with FastAPI, PostgreSQL, Redis, Celery, MinIO, Stripe, Nginx, Docker, and GitHub Actions.

This README is written so that a new developer can:

1. clone the repository,
2. configure environment variables,
3. run the project locally,
4. test the API,
5. optionally run the production Docker stack.

---

## What this project includes

- JWT authentication with access and refresh tokens
- user registration, activation, password reset, profile management
- movies catalog with search, filters, sorting, ratings, comments, favorites
- shopping cart and orders
- Stripe payment flow
- async background tasks with Celery + Redis
- object storage via MinIO (S3-compatible)
- PostgreSQL database with Alembic migrations
- Docker Compose setups for development, tests, and production
- CI/CD pipelines for testing, image build, and EC2 deployment

---

## Tech stack

- Python 3.10+
- FastAPI
- SQLAlchemy 2.x + asyncpg
- PostgreSQL 17
- Redis 7
- Celery 5
- MinIO
- Stripe
- Gunicorn + Uvicorn workers
- Nginx
- Poetry
- Docker / Docker Compose

---

## Project structure

```text
online_cinema_fast_api/
├── .github/workflows/          # CI/CD pipelines
├── commands/                   # shell scripts for app, migrations, deploy, etc.
├── configs/nginx/              # nginx config
├── docker/                     # dockerfiles for nginx, tests, mailhog, minio client
├── src/                        # application source code
├── docker-compose-dev.yml      # local development stack
├── docker-compose-tests.yml    # test stack
├── docker-compose-prod.yml     # production-like stack
├── Dockerfile
├── pyproject.toml
└── README.md
```

---

## Quick start with Docker (recommended)

This is the easiest way for anyone to run the project.

### 1. Clone the repository

```bash
git clone https://github.com/Artstrik/online_cinema_fast_api.git
cd online_cinema_fast_api
```

### 2. Create `.env`

Copy the example file:

```bash
cp .env.sample .env
```

For Windows PowerShell:

```powershell
Copy-Item .env.sample .env
```

Minimum variables already exist in `.env.sample`, but for a complete local run it is better to also add these values if they are missing:

```env
APP_BASE_URL=http://127.0.0.1:8080
STRIPE_SECRET_KEY=
STRIPE_PUBLISHABLE_KEY=
STRIPE_WEBHOOK_SECRET=
MAILHOG_API_PORT=8025
```

For local development you can keep Stripe keys empty unless you are testing payment integration.

### 3. Start the development stack

```bash
docker compose -f docker-compose-dev.yml up --build
```

### 4. Open the services

After the containers are healthy, the main services are available here:

- API: `http://127.0.0.1:8080`
- pgAdmin: `http://127.0.0.1:3333`
- MailHog UI: `http://127.0.0.1:8025`
- MinIO API: `http://127.0.0.1:9000`
- MinIO Console: `http://127.0.0.1:9001`
- Flower: `http://127.0.0.1:5555`

### 5. Stop the project

```bash
docker compose -f docker-compose-dev.yml down
```

To stop and remove volumes too:

```bash
docker compose -f docker-compose-dev.yml down -v
```

---

## First-run notes

### Migrations and seed data

The development stack includes a `migrator` service that applies Alembic migrations and populates the database.

If this is your first launch, give the containers a little time to initialize PostgreSQL and run migrations.

### Docs are protected

Swagger and ReDoc are not public in this project.

- Swagger: `/docs`
- ReDoc: `/redoc`
- OpenAPI JSON: `/api/v1/openapi.json`

These endpoints require an authenticated active user.

That means the usual first flow is:

1. register a user,
2. activate the account,
3. log in,
4. then access `/docs` with an authenticated session/token.

---

## How to run tests

The repository includes a separate test stack.

```bash
docker compose -f docker-compose-tests.yml up --build --abort-on-container-exit
```

This runs the e2e test flow in containers.

---

## Local run without Docker

This path is possible, but Docker is still the preferred option because the project depends on PostgreSQL, Redis, MinIO, and MailHog.

### Requirements

- Python 3.10+
- Poetry
- PostgreSQL
- Redis
- MinIO or another S3-compatible storage
- MailHog or SMTP server

### 1. Install dependencies

```bash
poetry install
```

### 2. Create `.env`

```bash
cp .env.sample .env
```

Then update the hosts so they point to your local services, for example:

```env
POSTGRES_HOST=127.0.0.1
POSTGRES_DB_PORT=5432
REDIS_HOST=127.0.0.1
REDIS_PORT=6379
MINIO_HOST=127.0.0.1
MINIO_PORT=9000
EMAIL_HOST=127.0.0.1
EMAIL_PORT=1025
APP_BASE_URL=http://127.0.0.1:8080
```

### 3. Apply migrations

Depending on your environment, you can run Alembic directly:

```bash
poetry run alembic upgrade head
```

### 4. Start the API

```bash
poetry run uvicorn src.main:app --host 0.0.0.0 --port 8080 --reload
```

### 5. Start Celery worker

```bash
poetry run celery -A src.celery_app.celery_app worker -l info
```

### 6. Start Celery beat

```bash
poetry run celery -A src.celery_app.celery_app beat -l info
```

This mode is mainly for contributors who want tighter local control.

---

## Environment variables

Core variables used by the application:

### PostgreSQL

```env
POSTGRES_DB=movies_db
POSTGRES_DB_PORT=5432
POSTGRES_USER=admin
POSTGRES_PASSWORD=some_password
POSTGRES_HOST=postgres_theater
```

### JWT

```env
SECRET_KEY_ACCESS=change_me_to_a_long_random_value
SECRET_KEY_REFRESH=change_me_to_a_long_random_value
JWT_SIGNING_ALGORITHM=HS256
```

### Email / MailHog

```env
EMAIL_HOST=mailhog_theater
EMAIL_PORT=1025
EMAIL_HOST_USER=testuser
EMAIL_HOST_PASSWORD=test_password
EMAIL_USE_TLS=False
MAILHOG_USER=admin
MAILHOG_PASSWORD=some_password
MAILHOG_API_PORT=8025
```

### MinIO / S3

```env
MINIO_ROOT_USER=minioadmin
MINIO_ROOT_PASSWORD=some_password
MINIO_HOST=minio-theater
MINIO_PORT=9000
MINIO_STORAGE=theater-storage
```

### Redis

```env
REDIS_HOST=redis_theater
REDIS_PORT=6379
REDIS_DB=0
```

### App / Stripe

```env
APP_BASE_URL=http://127.0.0.1:8080
STRIPE_SECRET_KEY=
STRIPE_PUBLISHABLE_KEY=
STRIPE_WEBHOOK_SECRET=
```

### pgAdmin

```env
PGADMIN_DEFAULT_EMAIL=admin@gmail.com
PGADMIN_DEFAULT_PASSWORD=admin
```

---

## Main API groups

The application is mounted under:

```text
/api/v1
```

Main route groups:

- `/api/v1/accounts`
- `/api/v1/profiles`
- `/api/v1/cart`
- `/api/v1/orders`
- `/api/v1/payments`
- movie endpoints under `/api/v1/...`
- movie interaction endpoints under `/api/v1/...`

Because OpenAPI is protected, the fastest way to explore endpoints is:

1. run the app,
2. create and authenticate a user,
3. open `/docs`.

---

## Development commands

### Start development stack

```bash
docker compose -f docker-compose-dev.yml up --build
```

### Rebuild from scratch

```bash
docker compose -f docker-compose-dev.yml down -v
docker compose -f docker-compose-dev.yml up --build
```

### Run tests

```bash
docker compose -f docker-compose-tests.yml up --build --abort-on-container-exit
```

### Lint

```bash
poetry run flake8 .
```

---

## Production-like run on one machine

If someone wants to simulate production locally or on a VM:

### 1. Prepare env files

Create project `.env`:

```bash
cp .env.sample .env
```

Check the Nginx env file too:

```text
docker/nginx/.env
```

The repository currently expects values such as:

```env
API_USER=admin
API_PASSWORD=strong_password_123
```

### 2. Start production stack

```bash
docker compose -f docker-compose-prod.yml up --build -d
```

### 3. Open the app

By default Nginx exposes the app on:

- `http://127.0.0.1`

---

## CI/CD summary

### CI

The CI pipeline:

- runs on `develop` and `main`
- installs Poetry dependencies
- runs `flake8`
- runs tests using `docker-compose-tests.yml`

### CD

The CD pipeline:

- runs on push to `main`
- connects to EC2 using `appleboy/ssh-action`
- updates the repo on the server
- pulls Docker image from Docker Hub
- recreates the production stack

Expected server project path in the current workflow:

```text
/home/ubuntu/src/online_cinema_fast_api
```

---

## Deployment script

The repository contains:

```text
commands/deploy.sh
```

It currently:

- enters `/home/ubuntu/src/online_cinema_fast_api`
- fetches `origin/main`
- resets the local copy to `origin/main`
- runs `docker compose -f docker-compose-prod.yml up -d --build`

Make the script executable if needed:

```bash
chmod +x commands/deploy.sh
```

Run it on the server:

```bash
./commands/deploy.sh
```

---

## Troubleshooting

### `Error: missing server host` in GitHub Actions

Your `EC2_HOST` secret is empty, missing, or not available to the workflow.

### `cd: /home/.../online_cinema_fast_api: No such file or directory`

The deploy workflow points to the wrong server path. The current valid path is:

```text
/home/ubuntu/src/online_cinema_fast_api
```

### `docker-compose-prod.yml: no such file or directory`

Usually caused by running deploy commands outside the project root.

### `dos2unix: No such file or directory`

You are likely using the wrong relative path. In this repository the deploy script is located at:

```text
./commands/deploy.sh
```

### Swagger `/docs` returns auth error

This is expected. Docs are intentionally protected and require an authenticated active user.

### Payments do not work locally

Stripe keys are missing or webhooks are not configured. For basic local development, leave Stripe disabled unless you are specifically testing payments.

---

## Recommended onboarding flow for a new developer

If someone downloads this repository for the first time, this is the best path:

```bash
git clone https://github.com/Artstrik/online_cinema_fast_api.git
cd online_cinema_fast_api
cp .env.sample .env
docker compose -f docker-compose-dev.yml up --build
```

Then open:

- API: `http://127.0.0.1:8080`
- MailHog: `http://127.0.0.1:8025`
- MinIO Console: `http://127.0.0.1:9001`
- pgAdmin: `http://127.0.0.1:3333`

---

## Author

**Artem Shlychkin**

Backend developer focused on FastAPI, async Python, Dockerized services, and production-style backend architecture.