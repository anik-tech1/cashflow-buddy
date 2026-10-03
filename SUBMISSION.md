# CashflowBuddy: Privacy-First Financial Assistant for Freelancers

**Built with:** TabPFN + Google Gemma + LangGraph + Streamlit  
**For:** Hacktoberfest 2026  
**License:** MIT  
**GitHub:** [cashflow-buddy](https://github.com/yourusername/cashflow-buddy)

---

## The Problem

Freelancers face an impossible choice:
- Your NDA contracts forbid uploading client names to ChatGPT or Anthropic
- You need AI help predicting cash crunches and prioritizing collections
- Commercial financial APIs require uploading sensitive data or cost real money

**CashflowBuddy solves this** by running sensitive analysis on your laptop while using a remote GPU only for tasks that don't require PII.

---

## The Solution: Split-Brain Architecture

CashflowBuddy orchestrates a 4-step workflow that keeps your client data private:

```
Your Laptop (Private)                    Colab GPU (Ephemeral)
────────────────────                     ─────────────────────

1. TabPFN Forecast    ──(redacted)──►   3. Gemma LLM
   (Cash crunch risk)                       (Strategy)
                                        
2. PII Redactor       ──────────────►
   (Strip names)       
                                        
4. Rehydrator         ◄──(tokens)────
   (Restore names)
```

**The Promise:** Your client names never leave your PC.

### How It Works in 4 Steps

**Step 1: Local Risk Forecast**
- TabPFN (Prior Labs' ML model for spreadsheets) analyzes your historical spending and invoices
- Predicts: "75% chance of cash crunch this month" vs. "15% if you collect one invoice"
- Runs on your CPU, never touches the internet

**Step 2: Anonymize Before Sending**
- Script strips all client names, emails, and project data locally
- Replaces `BlueWave Health Media` with token `[CLIENT_INV-104]`
- Only anonymized data leaves your PC

**Step 3: Remote AI Strategy**
- Sends redacted forecast and ledger to Gemma on Colab's free T4 GPU
- Gemma generates 3 sections without ever knowing client names:
  - Risk assessment in plain English
  - Prioritized invoice collection queue (by token)
  - Polite payment reminder email (addressing `[CLIENT_INV-104]`)

**Step 4: Rehydrate Locally**
- Response returns to your PC with tokens only
- Local script swaps `[CLIENT_INV-104]` back to `BlueWave Health Media (ap@bluewavehealth.org)`
- You get personalized, ready-to-use action plan

---

## Why This Matters for Hacktoberfest

### 1. **Solves a Real Problem**
Most open-source financial tools either avoid AI entirely or demand API keys + internet uploads. CashflowBuddy shows a third way: privacy-first orchestration.

### 2. **Novel Architecture**
The split-brain pattern (local private CPU + remote GPU) is rarely seen in hackathons. It's production-relevant for any app handling sensitive data.

### 3. **Open-Source Stack**
- **TabPFN** (Prior Labs) – Fast ML for tabular data
- **Gemma** (Google) – Open-weight 2B/9B LLM
- **LangGraph** (LangChain) – Orchestration
- **Streamlit** – Dashboard UI
- **Cloudflare Tunnel** – Encrypted local-to-cloud bridge (free)

No paid APIs, no proprietary models.

### 4. **Production-Ready Code**
- Input validation (negative amounts, malformed CSVs)
- Retry logic with exponential backoff
- Graceful fallbacks (RandomForest if TabPFN unavailable)
- Comprehensive error handling
- 300+ lines of unit tests

### 5. **Great Documentation**
- `README.md` with architecture diagrams
- `ARCHITECTURE.md` explaining the 4-node workflow
- `CONTRIBUTING.md` with development guidelines
- Inline logging for debugging

---

## Quick Demo

### Setup (5 minutes)
```bash
git clone https://github.com/yourusername/cashflow-buddy
cd cashflow-buddy
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

### Run on Colab (one-time, ~2 minutes)
1. Open `colab_gpu_server.ipynb` in Google Colab
2. Run all cells → get tunnel URL (e.g., `https://random-words.trycloudflare.com`)
3. Paste URL into Streamlit sidebar

### Generate Plan
1. Adjust "Upcoming Expenses" and "Expected Invoices" (or leave defaults)
2. Click **"Run Open-Source Agent Graph"**
3. Get risk forecast, prioritized collection queue, and email drafts
4. View Privacy Inspector tab to confirm **zero client names crossed the tunnel**

---

## Key Features

| Feature | Details |
|---------|---------|
| **TabPFN Risk Forecast** | ML-based cash crunch probability (baseline vs. recovery scenarios) |
| **PII Redaction Shield** | Strips names/emails before sending to remote AI |
| **Gemma LLM Integration** | Remote inference on free Colab T4 GPU |
| **Local Rehydration** | Restores real client data on your PC |
| **Email Templates** | Auto-generate payment reminder drafts |
| **Multi-Month Forecast** | 3-month projected expenses & balance |
| **CSV Export** | Download forecasts for accounting software |
| **Privacy Inspector** | Audit exactly what leaves your PC |
| **Comprehensive Tests** | 300+ lines covering edge cases |
| **Docker Support** | Deploy locally or to cloud |

---

## What Gets Built

```
cashflow-buddy/
├── README.md                    # Getting started + architecture overview
├── ARCHITECTURE.md              # Deep dive: 4-node workflow, data flows, security
├── CONTRIBUTING.md              # Dev setup, code style, testing
├── DEPLOYMENT.md                # Docker, Railway, GCP, Vercel
├── LICENSE                      # MIT
├── Dockerfile                   # Containerized Streamlit app
├── app.py                       # Streamlit dashboard (4 tabs)
├── agent.py                     # LangGraph + TabPFN + PII redaction/rehydration
├── features.py                  # Email templates, forecasts, CSV export
├── seed_data.py                 # Sample data generation
├── colab_gpu_server.ipynb       # Ollama + Gemma setup for Colab
├── requirements.txt             # Dependencies
├── tests/
│   └── test_agent.py           # 300+ lines: TabPFN, redaction, rehydration, forecasts
├── invoices.csv                 # Sample invoice data (generated)
└── monthly_history.csv          # Sample historical data (generated)
```

---

## Error Handling & Resilience

✅ **Retry Logic** – 3 attempts with exponential backoff for Colab timeouts  
✅ **Graceful Fallbacks** – RandomForest if TabPFN unavailable  
✅ **Input Validation** – Reject negative expenses, malformed CSVs  
✅ **Comprehensive Logging** – Debug connection, CSV, and redaction issues  
✅ **Edge Cases** – Handle special characters in client names, missing columns

---

## Tech Stack Deep Dive

### Local Brain (Your CPU)
```python
# TabPFN for fast tabular ML
clf = TabPFNClassifier(device="cpu")
clf.fit(X_train, y_train)  # ~0.5s

# Regex-based PII redaction
anonymized = re.sub(r"[CLIENT_INV-104]", "[CLIENT_INV-104]", text)

# Graph orchestration
builder = StateGraph(CashflowState)
builder.add_node("local_tabpfn_forecast", node_tabpfn_forecast)
builder.add_node("local_pii_redactor", node_pii_redactor)
# ... connects 4 nodes in sequence
graph = builder.compile()
```

### Remote Brain (Colab GPU)
```python
# Ollama + Gemma on T4 GPU
llm = ChatOllama(
    base_url="https://tunnel-url",
    model="gemma2:9b",
    temperature=0.3,
    num_ctx=8192,
)
response = llm.invoke(prompt)  # ~5-15s
```

### Dashboard (Streamlit)
```python
# 4 tabs: Dashboard, Privacy, Emails, Forecast
st.tabs(["Agent Dashboard", "Zero-Trust Privacy Inspector", 
         "Email Templates", "Multi-Month Forecast"])

# Live metrics
st.metric("TabPFN Baseline Crunch Risk", "75%")
st.metric("Risk After Collection", "15%")

# Privacy audit trail
st.code(get_redacted_invoice_payload())
```

---

## Testing

### Coverage
- ✅ TabPFN vs. RandomForest fallback
- ✅ PII redaction (normal + special characters)
- ✅ PII rehydration (single + multiple tokens)
- ✅ Multi-month forecasting
- ✅ CSV parsing + validation
- ✅ Email template generation
- ✅ Error handling (missing files, invalid inputs)

### Run Tests
```bash
pytest tests/test_agent.py -v
```

---

## Deployment Options

### Local
```bash
streamlit run app.py
```

### Docker
```bash
docker build -t cashflow-buddy .
docker run -p 8501:8501 cashflow-buddy
```

### Cloud (Railway)
```bash
railway up
# Set COLAB_TUNNEL_URL in Railway dashboard
```

See `DEPLOYMENT.md` for Vercel, GCP, and Railway guides.

---

## Security & Privacy

| Data | Location | Encrypted? | Visible to AI? |
|------|----------|-----------|----------------|
| Client names | invoices.csv | At-rest | ❌ No (redacted) |
| Client emails | invoices.csv | At-rest | ❌ No (redacted) |
| Expenses | monthly.csv | At-rest | ✅ Yes (anonymized numbers) |
| Invoices | monthly.csv | At-rest | ✅ Yes (anonymized numbers) |
| Redacted ledger | Tunnel | In-transit (TLS 1.3) | ✅ Yes (tokens only) |
| Gemma response | Tunnel | In-transit (TLS 1.3) | Local rehydration |

**Key Principle:** PII never leaves your PC unencrypted or exposed.

---

## What I Learned Building This

1. **LangGraph orchestration** – State machines are great for multi-step AI workflows
2. **TabPFN magic** – Tabular ML is blazingly fast on small datasets
3. **Privacy architecture** – Design privacy in from the start, not as a patch
4. **Error handling** – Network timeouts and CSV parsing errors are common in real apps
5. **Testing split-brain systems** – Mocking remote services is critical

---

## Future Ideas

- [ ] Invoice PDF upload & parsing
- [ ] Automated SMTP email sending
- [ ] Stripe/Wave/Xero integration
- [ ] Multi-currency support
- [ ] Historical trend charts
- [ ] Collaboration (share with accountants)
- [ ] Mobile app (React Native)

---

## Credits

- **TabPFN** – Prior Labs (tabular prediction in <1 second on CPU)
- **Gemma** – Google DeepMind (open-weight LLM)
- **LangGraph** – LangChain (agent orchestration)
- **Streamlit** – Interactive dashboards without JavaScript
- **Cloudflare Tunnel** – Free, encrypted local-to-cloud bridge

---

## Links

- **GitHub:** https://github.com/yourusername/cashflow-buddy
- **Live Demo:** https://cashflow-buddy.streamlit.app (after deployment)
- **Architecture Diagram:** See ARCHITECTURE.md
- **Contributing:** See CONTRIBUTING.md

---

## Why This Matters

Most developers think "privacy" = encrypt everything. CashflowBuddy shows a deeper principle: **design your system so sensitive data never needs to cross untrusted boundaries in the first place.**

This pattern applies beyond finance: healthcare dashboards, legal docs, HR systems—anywhere PII and AI meet.

For Hacktoberfest, this is a project that:
- ✅ Solves a real problem
- ✅ Uses open-source tech creatively
- ✅ Demonstrates architectural thinking
- ✅ Includes tests and docs
- ✅ Is production-ready, not a toy

Happy collecting! 💰
