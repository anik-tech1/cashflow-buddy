# CashflowBuddy Backend Architecture

## Current Setup (What You Have Now)

```
┌─────────────────────────────────────────────────────────────┐
│                  Render (Frontend + Backend)                │
│                                                              │
│  Streamlit App (Frontend)                                   │
│  ├─ app.py → UI/Dashboard                                  │
│  ├─ agent.py → TabPFN ML logic (CPU)                       │
│  ├─ features.py → Email, forecast, export                  │
│  └─ Local CSV files (invoices.csv, monthly_history.csv)    │
│                                                              │
│  Everything runs ON THE SAME INSTANCE (Render)             │
└────────────────┬─────────────────────────────────────────────┘
                 │
        Cloudflare Tunnel (encrypted)
                 │
┌────────────────▼─────────────────────────────────────────────┐
│           Google Colab (Remote GPU)                          │
│                                                              │
│  Ollama + Gemma Model (T4 GPU)                             │
│  → Handles only LLM inference                              │
│  → Never sees client names (PII)                           │
└──────────────────────────────────────────────────────────────┘
```

**Reality:** CashflowBuddy is **NOT a traditional backend/frontend split**. It's:
- **Streamlit monolith** (frontend + business logic in one)
- **No separate backend API**
- **No database** (uses local CSV files)
- **Remote GPU only** for LLM inference (Colab)

---

## If You Want a Proper Backend API

You'd need to add:

### Option A: FastAPI Backend + React Frontend (Production)

```
┌──────────────────────────┐
│   React Frontend (Vercel)│
│   (Dashboard UI)         │
└──────────────┬───────────┘
               │ HTTP/JSON
┌──────────────▼───────────┐
│  FastAPI Backend (Render)│
│                          │
│  ├─ /api/forecast       │
│  ├─ /api/redact         │
│  ├─ /api/generate-email │
│  ├─ /api/gemma-prompt   │
│  └─ Database (PostgreSQL)
└──────────────┬───────────┘
               │ Encrypted
┌──────────────▼──────────────────┐
│  Google Colab (Gemma GPU)       │
└─────────────────────────────────┘
```

### Option B: Keep Streamlit, Add Backend (Hybrid)

```
┌──────────────────────────┐
│  Streamlit on Render     │
│  (Just UI frontend)      │
└──────────────┬───────────┘
               │
┌──────────────▼───────────┐
│  FastAPI on Render       │
│  (Business logic)        │
│  ├─ TabPFN inference     │
│  ├─ PII redaction        │
│  ├─ Database queries     │
│  └─ File handling        │
└──────────────┬───────────┘
               │
        ┌──────▼──────┐
        │  Database   │
        │ PostgreSQL  │
        └─────────────┘
```

---

## What Backend Services You Might Need

### 1. **Database** (if you want to persist user data)
- **PostgreSQL** on Render (`$15/mo`)
- **Supabase** (PostgreSQL + Auth, free tier available)
- **MongoDB Atlas** (NoSQL, free tier)

**Current:** Uses local CSV files (no database)

### 2. **File Storage** (if you want to store invoices in cloud)
- **AWS S3** (~$1/mo for small usage)
- **Supabase Storage** (free tier)
- **Google Cloud Storage**

**Current:** Files stored on Render instance (lost on redeploy)

### 3. **Authentication** (if you want user login)
- **Auth0** (free tier)
- **Supabase Auth** (free)
- **Firebase Auth** (free)

**Current:** No authentication (anyone can access)

### 4. **Background Jobs** (if you want scheduled tasks)
- **Render background workers** ($12+/mo)
- **Bull/Redis** (for job queues)
- **Celery** (async tasks)

**Current:** Everything synchronous (no scheduled tasks)

### 5. **LLM API** (if you don't want Colab)
- **OpenAI API** ($0.01-0.10 per request)
- **Anthropic Claude** ($0.003-0.06 per request)
- **Together AI** (cheaper open models)
- **Hugging Face Inference** (free for open models)

**Current:** Free Colab T4 GPU (best option)

---

## Recommendation: Keep Current Setup (It's Actually Better)

**Why CashflowBuddy's current architecture is smart:**

✅ **No backend to maintain** – Streamlit handles frontend + logic  
✅ **No database costs** – CSVs are free and encrypted locally  
✅ **No auth complexity** – Personal use (can add later)  
✅ **Free GPU** – Colab T4 is free (vs $0.10+ per API call)  
✅ **Privacy by design** – PII never leaves user's PC  
✅ **Simple deployment** – One-click Render deploy  

**Cost:** $0-7/mo (free tier or $7 Starter)

---

## When to Add Backend Services

| Need | Service | Cost | Difficulty |
|------|---------|------|-----------|
| Save invoices to cloud | Supabase Storage | Free | 1/5 |
| User login | Supabase Auth | Free | 2/5 |
| Multiple users | PostgreSQL | $15/mo | 3/5 |
| Scheduled reports | Render Workers | $12+/mo | 3/5 |
| Better LLM quality | OpenAI API | $0.01-0.10/call | 2/5 |

---

## If You REALLY Want a Backend API

Here's a minimal FastAPI backend you could add:

```python
# backend/main.py
from fastapi import FastAPI
from fastapi.responses import JSONResponse
import pandas as pd
from agent import compute_tabpfn_probabilities, get_redacted_invoice_payload

app = FastAPI()

@app.post("/api/forecast")
async def forecast(expenses: float, invoiced: float):
    result = compute_tabpfn_probabilities(expenses, invoiced)
    return JSONResponse(result)

@app.get("/api/ledger")
async def get_ledger():
    return {"ledger": get_redacted_invoice_payload()}

@app.post("/api/gemma-prompt")
async def gemma_inference(prompt: str, colab_url: str):
    # Call Gemma on Colab
    # Returns LLM response
    pass

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

Then:
- Deploy backend to Render
- Streamlit calls `/api/forecast` instead of local function
- But... it's MORE complex and slower (network latency)

---

## TL;DR

**Current CashflowBuddy Architecture:**

```
Frontend + Backend + Logic = All in Streamlit on Render
           ↓
        Colab GPU (only for LLM)
```

**This is actually ideal for:**
- Single-user or team use
- Privacy (no cloud database)
- Cost ($0-7/mo)
- Simplicity (one deployment)

**You DON'T need a separate backend API unless you want:**
- Multi-user with login
- Data persistence across deployments
- Scheduled/async jobs
- Microservices architecture

---

## What Should You Do Now?

**Option 1: Keep It Simple (Recommended)**
- Deploy current Streamlit + Colab setup to Render ✅
- Data saved locally in Render instance
- Works great for 1-5 users
- Cost: $0-7/mo

**Option 2: Add Persistence (Later)**
- Add PostgreSQL ($15/mo) + user auth
- Save invoices to database
- Multi-user support
- Still use same Streamlit frontend

**Option 3: Full Architecture Refactor (Only if needed)**
- Split into React frontend + FastAPI backend
- Add all the backend services
- But you lose simplicity + privacy benefits
- Cost: $50+/mo

---

## Questions?

- Want to add a database?
- Need user authentication?
- Want to scale to multiple users?
- Need async job scheduling?

Let me know and I can set up any of these!
