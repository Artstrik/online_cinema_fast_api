# 🎬 FastAPI Movies E-commerce Platform

<div align="center">

![FastAPI](https://img.shields.io/badge/FastAPI-0.109+-009688?style=flat-square&logo=fastapi)
![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat-square&logo=python)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-4169E1?style=flat-square&logo=postgresql)
![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)
![Status](https://img.shields.io/badge/Status-In%20Development-yellow?style=flat-square)

**Modern e-commerce platform for movies built with FastAPI**

</div>

---

## 📖 About

A full-featured e-commerce platform for digital movie sales with user authentication, shopping cart, payment processing, and more.

## ✨ Planned Features

- 🔐 User authentication and authorization
- 🎬 Movie catalog with search
- 🛒 Shopping cart
- 💳 Payment processing (Stripe)
- ⭐ Ratings and reviews
- 📧 Email notifications

## 🛠 Tech Stack

- **Backend**: FastAPI, Python 3.11+
- **Database**: PostgreSQL, SQLAlchemy (async)
- **Cache**: Redis
- **Queue**: Celery
- **Testing**: pytest

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Poetry
- Docker

### Installation

```bash
# Clone repository
git clone <repo-url>
cd fastapi-movies-ecommerce

# Install dependencies
poetry install

# Copy environment file
cp .env.sample .env

# Start database
docker compose up -d

# Run migrations
poetry run alembic upgrade head

# Start application
poetry run uvicorn src.main:app --reload
```

Visit http://localhost:8000/docs for API documentation.

## 📁 Project Structure

```
src/
├── config/          # Configuration
├── database/        # Models & migrations
├── routes/          # API endpoints
├── schemas/         # Pydantic schemas
└── tests/           # Tests
```

## 🧪 Testing

```bash
poetry run pytest
```

## 📚 Documentation

- API Docs: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 🤝 Contributing

Contributions welcome! Please open an issue or submit a PR.

## 📄 License

MIT License - see LICENSE file for details.

---

<div align="center">
Made with ❤️ using FastAPI
</div>