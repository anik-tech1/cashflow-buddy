# CashflowBuddy: Privacy-First Financial Assistant for Freelancers

A split-brain AI system that predicts cashflow risk, prioritizes overdue invoices, and generates collection emails—**without ever uploading your client names to the cloud.**

Built with **TabPFN** (local CPU), **Google Gemma** (remote GPU), and **LangGraph** orchestration for Hacktoberfest 2026.

## The Problem

Freelancers face a trust paradox:
- Their NDAs forbid uploading client data to ChatGPT or Anthropic
- They need AI help analyzing invoices, predicting cash crunches, and drafting collection emails
- Existing financial tools either don't use AI, or require sharing sensitive data

## The Solution: Split-Brain Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Your Laptop (Private)                     │
│                                                              │
│  1. TabPFN Model       2. PII Redactor     4. Rehydrator    │
│  (Spreadsheet Math)    (Name Stripping)    (Restore Names)  │
│                                                              │
│  invoices.csv ──────► [CLIENT_INV-104] ──────┐              │
│  monthly_history.csv  (Anonymized) ──────────┤              │
│                                               │              │
└───────────────────────────────────────────────┼──────────────┘
                                                │
                                    3. Cloudflare Tunnel
                                    (Encrypted, No Names)
                                                │
┌───────────────────────────────────────────────▼──────────────┐
│                   Google Colab (Free T4 GPU)                 │
│                                                              │
│  Ollama + Gemma Model                                        │
│  (Writes strategy, never sees client names)                  │
│                                                              │
│  "Rank overdue invoices... Contact [CLIENT_INV-104]..."     │
└──────────────────────────────────────────────────────────────┘
```

**Key Promise:** Zero client PII ever leaves your PC unencrypted.

## Features

- **TabPFN Risk Forecast** – Predicts cash crunch probability based on historical spending and payment delays (runs on local CPU)
- **PII Redaction Shield** – Strips client names, emails, and project data before sending to remote AI
- **Gemma LLM Orchestration** – Remote inference generates prioritized collection plan and email drafts
- **Local PII Rehydration** – Restores real names in the final output (happens on your PC)
- **Interactive Dashboard** – Streamlit UI with risk metrics, invoice tables, and Privacy Inspector tab
- **Privacy Audit Trail** – See exactly what gets anonymized and sent over the tunnel

## Quick Start

### Prerequisites
- Python 3.9+
- Google Colab account (free T4 GPU)
- Cloudflare Tunnel (`trycloudflare.com` – free)

### 1. Clone & Install

```bash
git clone https://github.com/yourusername/cashflow-buddy.git
cd cashflow-buddy
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Set Up Colab GPU (One-Time)

Open `colab_gpu_server.ipynb` in Google Colab and run all cells. This:
- Installs Ollama
- Downloads Gemma model
- Creates a private Cloudflare Tunnel (e.g., `https://random-words.trycloudflare.com`)
- Keeps the tunnel alive for 8 hours

Copy the tunnel URL.

### 3. Launch the App

```bash
streamlit run app.py
```

Visit `http://localhost:8501` in your browser.

### 4. Run the Agent

1. Paste your Colab tunnel URL in the left sidebar
2. Adjust "Upcoming Monthly Expenses" and "Expected New Invoices" (defaults show sample data)
3. Click **"Run Open-Source Agent Graph"**
4. Watch the Privacy Inspector tab to confirm no client names leave your PC

## Architecture Walkthrough

### Step 1: Local Risk Forecast (TabPFN)
- Reads `monthly_history.csv` (16 months of expenses, invoices, late-payment rates)
- Runs TabPFN classifier on local CPU (falls back to RandomForest if unavailable)
- Outputs: "75% chance of cash crunch if no invoices collected; 15% if you collect INV-104"

### Step 2: PII Redaction (Local)
- Reads `invoices.csv` with real client names, emails, project info
- Creates anonymized ledger: `[CLIENT_INV-104]` instead of "BlueWave Health Media"
- Only the anonymized ledger leaves your PC

### Step 3: Remote LLM Inference (Colab GPU)
- Sends TabPFN forecast + anonymized ledger through encrypted Cloudflare tunnel
- Gemma generates 3 sections:
  - Cashflow Risk Assessment (plain English)
  - Prioritized Collection Queue (which invoices to chase first)
  - Ready-to-Send Email (polite payment reminder)

### Step 4: Local Rehydration (Your PC)
- Receives anonymized response from Gemma
- Swaps `[CLIENT_INV-104]` back to "BlueWave Health Media (ap@bluewavehealth.org)"
- Outputs personalized, actionable plan ready to copy-paste

## File Reference

| File | Purpose |
|------|---------|
| `app.py` | Streamlit dashboard with UI, metrics, Privacy Inspector |
| `agent.py` | LangGraph orchestration, TabPFN inference, PII redaction/rehydration |
| `seed_data.py` | Generates sample `invoices.csv` and `monthly_history.csv` |
| `colab_gpu_server.ipynb` | Runs on Google Colab; hosts Ollama + Gemma model via tunnel |
| `requirements.txt` | Python dependencies |
| `invoices.csv` | Your invoice ledger (generated or provided) |
| `monthly_history.csv` | Historical monthly expenses, invoices, crash flags (generated or provided) |

## Data Format

### invoices.csv
```
invoice_id,client_name,contact_email,project_name,amount,status,days_overdue
INV-104,BlueWave Health Media,ap@bluewavehealth.org,Dashboard Redesign,1450.00,overdue,39
INV-101,Acme Corp,billing@acme.com,Mobile App,2100.00,overdue,25
INV-105,Tech Startup,finance@techstartup.io,API Development,800.00,paid,0
```

### monthly_history.csv
```
month,expenses,invoiced,late_ratio,had_cash_crunch
2025-06,3200.00,3100.00,0.15,0
2025-07,3350.00,3600.00,0.22,0
2025-08,3500.00,2900.00,0.35,1
```

## Environment Variables

Optional (for production):
```bash
COLAB_TUNNEL_URL=https://random-words.trycloudflare.com
```

## Security Notes

- **No API Keys Required** – Uses free Colab GPU and Cloudflare Tunnel
- **No Third-Party Analytics** – All code runs locally except Gemma inference
- **Cloudflare Tunnel is Encrypted** – TLS 1.3 in-transit encryption
- **PII Never Logged** – Redaction happens before network calls

## Testing

```bash
pytest tests/
```

Tests cover:
- TabPFN vs. RandomForest fallback
- PII redaction edge cases (special characters, multiple invoices)
- Graph workflow orchestration
- CSV parsing and validation

## Deployment

### Docker

```bash
docker build -t cashflow-buddy .
docker run -p 8501:8501 cashflow-buddy
```

### Railway / Vercel

See `DEPLOYMENT.md` for cloud deployment guides (Docker, Railway, Vercel).

## Contributing

Contributions welcome! See `CONTRIBUTING.md` for guidelines.

### Ideas
- Multi-currency support
- Invoice template generator
- Automated email sending (SMTP integration)
- Historical trend charts
- Multi-tenant (org-level) support
- Mobile app
- Integration with Stripe, Wave, or Xero

## Why Hacktoberfest?

This project demonstrates:
1. **Novel Architecture** – Split-brain AI avoids uploading sensitive data to commercial APIs
2. **Real-World Problem** – Addresses genuine NDA + privacy constraints for freelancers
3. **Open-Source Stack** – TabPFN, Gemma, LangGraph, Streamlit (no paid deps)
4. **Privacy-by-Design** – Security is architectural, not bolted on
5. **Production-Relevant** – Retry logic, error handling, testing, and observability included

## Credits

- **TabPFN** – Prior Labs (tabular prediction in <1 second)
- **Gemma** – Google DeepMind (open-weight LLM)
- **LangGraph** – LangChain (graph-based orchestration)
- **Streamlit** – Interactive data apps
- **Cloudflare Tunnel** – Secure local-to-cloud bridge

## License

MIT – See `LICENSE` file.

## Changelog

### v1.0.0 (Oct 2026)
- Initial split-brain architecture
- TabPFN risk forecasting
- PII redaction + rehydration
- Gemma integration via Colab
- Streamlit dashboard with Privacy Inspector
- Full test suite

---

**Have questions?** Open an issue or check the [Architecture Guide](ARCHITECTURE.md).
