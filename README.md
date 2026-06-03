<div align="center">

# 🎯 IELTS Platform

[![CI/CD Pipeline](https://github.com/baxtiyorovanozima02/ielts-platform/actions/workflows/ci.yml/badge.svg)](https://github.com/baxtiyorovanozima02/ielts-platform/actions)
[![Python](https://img.shields.io/badge/Python-3.11-blue?logo=python)](https://python.org)
[![Django](https://img.shields.io/badge/Django-4.x-green?logo=django)](https://djangoproject.com)
[![Docker](https://img.shields.io/badge/Docker-ready-blue?logo=docker)](https://docker.com)
[![License](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)

**AI-powered IELTS preparation platform for Central Asia students 🌍**

*Mock tests • AI feedback • Personal study plan • Progress tracking*

</div>

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| 🧠 **AI Scoring** | Instant Writing & Speaking feedback |
| 📝 **Mock Tests** | All 4 IELTS sections (R/L/W/S) |
| 📊 **Progress Tracking** | Band score history & weak area analysis |
| 📅 **Study Plan** | Auto-generated personal daily schedule |
| 📚 **Vocabulary** | Spaced repetition system |
| 🤖 **Telegram Bot** | Practice anywhere via Telegram |
| 💳 **Local Payments** | Click & Payme integration |

---

## 🛠 Tech Stack

| Layer | Tools |
|-------|-------|
| 🔧 Backend | Python, Django, DRF |
| 🔐 Auth | JWT, Djoser |
| 🗄️ Database | PostgreSQL |
| ⚙️ Async | Celery, Redis |
| 🚀 DevOps | Docker, NGINX, AWS EC2 |
| 🤖 Bot | python-telegram-bot |

---

## 🚀 Quick Start

### 1. Clone the repo
```bash
git clone https://github.com/baxtiyorovanozima02/ielts-platform.git
cd ielts-platform
```

### 2. Setup environment
```bash
cp .env.example .env
# .env faylini o'zingizga moslashtiring
```

### 3. Run with Docker
```bash
docker-compose up --build -d
```

### 4. Apply migrations
```bash
docker exec -it ielts_web python manage.py migrate
```

### 5. Create superuser
```bash
docker exec -it ielts_web python manage.py createsuperuser
```

🎉 **Done!** Open `http://localhost` in your browser.

---

## 📡 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/auth/jwt/create/` | Login |
| POST | `/api/v1/auth/users/` | Register |
| GET | `/api/v1/tests/` | Get all tests |
| POST | `/api/v1/tests/writing/evaluate/` | AI Writing evaluation |
| POST | `/api/v1/tests/speaking/evaluate/` | AI Speaking evaluation |
| GET | `/api/v1/statistics/overall/` | User statistics |
| GET/POST | `/api/v1/vocabulary/` | Vocabulary list |
| GET | `/api/v1/billing/plans/` | Subscription plans |

📖 Full docs: `http://localhost/swagger/`

---

## 🧪 Running Tests

```bash
docker exec -it ielts_web python manage.py test apps --verbosity=2
```

✅ 42 tests — all passing!

---

## 🗺️ Roadmap

- [x] Project setup & Custom User Model
- [x] JWT Authentication & Djoser
- [x] Mock test engine (R/L/W/S)
- [x] AI Writing & Speaking evaluation
- [x] Celery async tasks
- [x] Statistics & weak area analysis
- [x] Vocabulary module
- [x] Telegram Bot integration
- [x] Billing & subscription plans
- [x] Docker + NGINX deploy
- [x] CI/CD pipeline (GitHub Actions)
- [ ] AWS EC2 production deploy
- [ ] Click & Payme payment gateway

---

## ⚙️ Environment Variables

```env
SECRET_KEY=your-secret-key
DEBUG=False
DB_NAME=ielts_db
DB_USER=postgres
DB_PASSWORD=yourpassword
DB_HOST=db
DB_PORT=5432
REDIS_URL=redis://redis:6379/0
OPENAI_API_KEY=your-openai-key
TELEGRAM_BOT_TOKEN=your-bot-token
```

---

<div align="center">

### 🆚 Why Choose Us?

| Feature | This Platform | IELTS.gg |
|---------|:---:|:---:|
| AI Writing/Speaking | ✅ | ✅ |
| Telegram Bot | ✅ | ❌ |
| Local Payments | ✅ | ❌ |
| Uzbek Interface | ✅ | ❌ |
| Price | ✅ Affordable | ❌ $20-50/mo |

---

**Made with ❤️ by [Nozima](https://github.com/baxtiyorovanozima02)**

⭐ *If you like this project, give it a star!* ⭐

</div>