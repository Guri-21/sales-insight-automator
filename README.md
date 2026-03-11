# 📊 Sales Insight Automator

> **Upload sales data → AI generates an executive brief → Delivered to your inbox.**
> Built for the Rabbitt AI sales team to transform raw CSV/XLSX data into actionable intelligence.

**👨‍💻 Built by: Gurnoor Partap Singh Bhogal**

[![CI Pipeline](https://github.com/your-org/sales-insight-automator/actions/workflows/ci.yml/badge.svg)](https://github.com/your-org/sales-insight-automator/actions)

---

## 🏗️ Architecture

```
┌────────────────────┐    POST /api/upload     ┌────────────────────┐
│  React SPA (Vite)  │ ─────────────────────►  │  FastAPI Backend   │
│  Port 3000 / 5173  │ ◄─────────────────────  │  Port 8000         │
└────────────────────┘    JSON response         ├────────────────────┤
                                                │ 1. Parse CSV/XLSX  │
                                                │ 2. Groq AI (Llama 3) │
                                                │ 3. Send via Resend │
                                                │ 4. Swagger @ /docs │
                                                └────────────────────┘
```

## 🚀 Quick Start with Docker Compose

### Prerequisites
- Docker & Docker Compose
- API keys: [Groq](https://console.groq.com) + [Resend](https://resend.com)

### Steps

```bash
# 1. Clone the repository
git clone https://github.com/your-org/sales-insight-automator.git
cd sales-insight-automator

# 2. Configure environment
cp .env.example .env
# Edit .env and add your GROQ_API_KEY and RESEND_API_KEY

# 3. Start the stack
docker-compose up --build

# 4. Open the app
# Frontend: http://localhost:3000
# Backend Swagger: http://localhost:8000/docs
```

### Development Mode (without Docker)

```bash
# Backend
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000

# Frontend (new terminal)
cd frontend
npm install
npm run dev
# Opens at http://localhost:5173 (API proxied to :8000)
```

---

## 🔒 Security Approach

| Layer | Implementation |
|-------|---------------|
| **Rate Limiting** | 10 requests/minute per IP via `slowapi` |
| **File Validation** | Whitelist `.csv`/`.xlsx` only, max 10MB, structure checks |
| **Input Sanitization** | Email validation via `email-validator`, no raw user input in prompts |
| **CORS** | Configurable allowed origins (locked in production) |
| **API Key Auth** | Optional `X-API-Key` header auth (toggle via `API_KEY_REQUIRED`) |
| **Docker Security** | Non-root user in backend container |
| **HTTP Headers** | `X-Frame-Options`, `X-Content-Type-Options`, `X-XSS-Protection` via nginx |
| **Error Handling** | Global exception handler — no stack traces leaked to client |

---

## 📡 API Reference

### `GET /api/health`
Health check endpoint returning service status.

```json
{
  "status": "healthy",
  "version": "1.0.0",
  "services": {
    "ai_engine": "configured",
    "email_service": "configured"
  }
}
```

### `POST /api/upload`
Upload a sales file and trigger AI processing + email delivery.

| Parameter | Type | Description |
|-----------|------|-------------|
| `file` | File | `.csv` or `.xlsx` file (max 10MB) |
| `email` | string | Recipient email address |

**Success Response (200):**
```json
{
  "status": "success",
  "message": "Insight brief generated and sent to user@example.com",
  "summary_preview": "Executive Summary: Q3 revenue grew by 12%...",
  "email_status": { "status": "sent", "email_id": "abc123" },
  "data_shape": { "rows": 150, "columns": 8 }
}
```

**Full interactive documentation:** [http://localhost:8000/docs](http://localhost:8000/docs)

---

## 🧪 Testing

```bash
# Backend tests
cd backend
python -m pytest tests/ -v

# Lint
cd backend && ruff check .
cd frontend && npx eslint src/
```

---

## 🐳 Docker Image Optimization

| Image | Base | Strategy | Approx. Size |
|-------|------|----------|-------------|
| Backend | `python:3.11-slim` | Dependency layer caching, no-cache pip | ~250MB |
| Frontend | `nginx:1.27-alpine` | Multi-stage (Node build → alpine serve) | ~40MB |

---

## 🔄 CI/CD Pipeline

The GitHub Actions pipeline (`.github/workflows/ci.yml`) triggers on:
- **Pull Requests** to `main`
- **Pushes** to `main`

**Jobs:**
1. **Backend Checks**: Ruff lint + format check, pytest
2. **Frontend Checks**: npm install + Vite build
3. **Docker Validation**: Build both images, verify sizes

---

## ☁️ Deployment

### Backend → Render
1. Connect your GitHub repo at [render.com](https://render.com)
2. The `render.yaml` blueprint auto-configures the service
3. Add `GROQ_API_KEY` and `RESEND_API_KEY` as environment variables

### Frontend → Vercel
1. Import the `frontend/` directory at [vercel.com](https://vercel.com)
2. Set `VITE_API_URL` to your Render backend URL
3. The `vercel.json` handles API rewrites and security headers

---

## 📁 Project Structure

```
sales-insight-automator/
├── backend/
│   ├── main.py                  # FastAPI app + endpoints
│   ├── services/
│   │   ├── file_parser.py       # CSV/XLSX parsing & validation
│   │   ├── ai_service.py        # Groq (Llama 3.3) integration
│   │   └── email_service.py     # Resend email delivery
│   ├── middleware/
│   │   └── security.py          # Rate limiting, API key auth
│   ├── tests/
│   │   └── test_api.py          # API & unit tests
│   ├── Dockerfile               # Multi-stage Python image
│   ├── requirements.txt         # Python dependencies
│   └── ruff.toml                # Linter config
├── frontend/
│   ├── src/
│   │   ├── App.jsx              # Main SPA component
│   │   ├── main.jsx             # React entry point
│   │   ├── index.css            # Design system
│   │   └── components/
│   │       ├── FileUploader.jsx # Drag-and-drop upload
│   │       └── StatusDisplay.jsx# Progress/success/error
│   ├── Dockerfile               # Multi-stage Node → nginx
│   ├── nginx.conf               # SPA routing + security
│   ├── vercel.json              # Vercel deployment config
│   └── package.json             # Node dependencies
├── .github/workflows/
│   └── ci.yml                   # CI/CD pipeline
├── docker-compose.yml           # Full stack orchestration
├── render.yaml                  # Render deployment blueprint
├── .env.example                 # Configuration template
├── .gitignore                   # Git ignore rules
└── README.md                    # This file
```

---

## ⚙️ Environment Variables

See [`.env.example`](.env.example) for all configuration keys with descriptions.

| Variable | Required | Description |
|----------|----------|-------------|
| `GROQ_API_KEY` | ✅ | Groq API key |
| `RESEND_API_KEY` | ✅ | Resend email service key |
| `SENDER_EMAIL` | ❌ | Sender email (default: `onboarding@resend.dev`) |
| `API_KEY_REQUIRED` | ❌ | Enable API key auth (default: `false`) |
| `API_KEY` | ❌ | API key value (if auth enabled) |
| `CORS_ORIGINS` | ❌ | Allowed origins (default: `*`) |
| `MAX_FILE_SIZE_MB` | ❌ | Max upload size (default: `10`) |
| `VITE_API_URL` | ❌ | Backend URL for frontend (default: `""`) |

---

