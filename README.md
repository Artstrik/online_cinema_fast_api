# 🎬 Online Cinema API

Production-ready backend service for an **Online Cinema platform** built with **FastAPI**.

The system allows users to browse movies, manage favorites, purchase movies, and pay for them using Stripe.
The platform includes a complete backend architecture with authentication, role-based access control, asynchronous processing, and containerized infrastructure.

---

# 🚀 Features

## Authentication & Authorization

* User registration with **email activation**
* **JWT authentication** (access + refresh tokens)
* Password reset via email
* Password change with validation
* Role-based access control

User roles:

* **USER** – standard platform user
* **MODERATOR** – can manage movies and catalog
* **ADMIN** – full system access including user management

---

# 🎬 Movies Catalog

Users can:

* Browse movies with **pagination**
* View movie details
* Search movies by:

  * title
  * description
  * actor
  * director
* Filter movies by:

  * release year
  * rating
* Sort movies by:

  * price
  * popularity
  * release date

Additional features:

* Like / dislike movies
* Rate movies (10-point scale)
* Write comments
* Add movies to favorites
* View genres with movie counts

Moderators can:

* Create movies
* Update movies
* Delete movies (if not purchased)
* Manage genres, actors, and directors

---

# 🛒 Shopping Cart

Users can:

* Add movies to cart
* Remove movies
* Clear cart
* View cart contents

Validation rules:

* Prevent duplicate movies
* Prevent purchasing already owned movies
* Ensure all movies are available

---

# 📦 Orders

Users can:

* Create orders from cart
* View order history
* Cancel orders before payment

Order statuses:

```
pending
paid
canceled
```

Each order stores:

* list of purchased movies
* price at order time
* total order cost

---

# 💳 Payments

Payments are processed via **Stripe**.

Features:

* Stripe Checkout integration
* Payment confirmation
* Payment history
* Webhook validation
* Automatic order status updates

Payment statuses:

```
successful
canceled
refunded
```

---

# 🏗 Architecture

The project follows **modular backend architecture** with clear separation of responsibilities between API layer, business logic, infrastructure services, and database access.

Project structure:

```
online_cinema_fast_api
│
├── .github
│   └── workflows
│       ├── ci_pipeline.yml
│       └── cd_pipeline.yml
│
├── commands                    # Utility scripts for running services
│   ├── run_celery_beat.sh
│   ├── run_celery_workers.sh
│   ├── run_migrations.sh
│   ├── run_web_server_dev.sh
│   ├── run_web_server_prod.sh
│   ├── set_nginx_basic_auth.sh
│   ├── setup_mailhog_auth.sh
│   └── setup_minio.sh
│
├── configs
│   └── nginx
│       └── nginx.conf
│
├── docker                      # Docker images for infrastructure
│   ├── mailhog
│   │   └── Dockerfile
│   │
│   ├── minio_mc
│   │   └── Dockerfile
│   │
│   ├── nginx
│   │   ├── Dockerfile
│   │   └── .env.sample
│   │
│   └── tests
│       └── Dockerfile
│
├── src                         # Application source code
│
│   ├── config
│   │   ├── dependencies.py
│   │   └── settings.py
│   │
│   ├── database
│   │   ├── migrations
│   │   ├── models
│   │   ├── seed_data
│   │   ├── source
│   │   ├── validators
│   │   ├── populate.py
│   │   ├── session_postgresql.py
│   │   └── session_sqlite.py
│   │
│   ├── exceptions
│   │   ├── email.py
│   │   ├── security.py
│   │   └── storage.py
│   │
│   ├── integrations
│   │   └── stripe_client.py
│   │
│   ├── notifications
│   │   ├── emails.py
│   │   ├── interfaces.py
│   │   └── templates
│   │
│   ├── routes
│   │   ├── accounts.py
│   │   ├── cart.py
│   │   ├── movie_interaction.py
│   │   ├── movies.py
│   │   ├── orders.py
│   │   ├── payments.py
│   │   └── profiles.py
│   │
│   ├── schemas
│   │   ├── accounts.py
│   │   ├── cart.py
│   │   ├── movie_interactions.py
│   │   ├── movies.py
│   │   ├── orders.py
│   │   ├── payments.py
│   │   └── profiles.py
│   │
│   ├── security
│   │   ├── http.py
│   │   ├── interfaces.py
│   │   ├── passwords.py
│   │   ├── token_manager.py
│   │   └── utils.py
│   │
│   ├── storages
│   │   ├── interfaces.py
│   │   └── s3.py
│   │
│   ├── tasks
│   │   └── cleanup_tasks.py
│   │
│   ├── tests
│   │   ├── doubles
│   │   ├── test_e2e
│   │   └── test_integration
│   │
│   ├── validation
│   │   ├── password.py
│   │   └── profile.py
│   │
│   ├── celery_app.py
│   └── main.py
│
├── docker-compose-dev.yml
├── docker-compose-prod.yml
├── docker-compose-tests.yml
│
├── Dockerfile
├── init.sql
│
├── pyproject.toml
├── poetry.lock
│
└── README.md
```

Architecture layers:

**API Layer**

* FastAPI routes
* request validation
* authentication dependencies

**Domain / Business Logic**

* services
* validation rules
* application logic

**Infrastructure Layer**

* Stripe integration
* Celery tasks
* email notifications
* S3 storage (MinIO)

**Persistence Layer**

* PostgreSQL
* SQLAlchemy models
* migrations

---

# 🛠 Tech Stack

### Backend

* FastAPI
* Python 3.11
* SQLAlchemy (Async)
* PostgreSQL

### Infrastructure

* Docker
* Docker Compose
* Nginx
* Redis
* Celery
* MinIO (S3 compatible storage)

### Authentication

* JWT
* OAuth2

### Payments

* Stripe

### CI/CD

* GitHub Actions
* AWS EC2

### Dependency Management

* Poetry

---

# 📦 Installation

Clone repository

```
git clone https://github.com/Artstrik/online_cinema_fast_api.git
cd online_cinema_fast_api
```

Install dependencies

```
poetry install
```

Run migrations

```
alembic upgrade head
```

Run application

```
uvicorn src.main:app --reload
```

---

# 🐳 Docker Setup

Run the entire system with one command:

```
docker compose up --build
```

This will start:

* FastAPI
* PostgreSQL
* Redis
* Celery worker
* Celery beat
* MinIO
* Nginx

---

# ☁️ Production Deployment

The project supports deployment to **AWS EC2**.

Production stack:

```
EC2
│
├── Nginx
├── Docker Compose
│
├── FastAPI
├── Redis
├── Celery
├── PostgreSQL
└── MinIO
```

Deployment is automated using **GitHub Actions CI/CD**.

Pipeline:

```
push → CI
lint
tests
docker build

↓

CD
deploy to EC2
```

---

# 🧪 Testing

The project includes several testing layers.

Unit Tests
Integration Tests
End-to-End Tests

Run tests:

```
pytest
```

---

# 👨‍💻 Author

**Artem Shlychkin**

Backend Developer
Python | FastAPI | Docker | AWS

GitHub
https://github.com/Artstrik

---

# 📜 License

This project is licensed under the MIT License.
