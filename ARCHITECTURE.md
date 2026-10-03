# CashflowBuddy Architecture

## High-Level Overview

CashflowBuddy is a **split-brain financial assistant** that combines local CPU computation with remote GPU inference while maintaining strict PII privacy boundaries.

```
┌─────────────────────────────────────┐
│     Your Laptop (Private Zone)      │
│                                     │
│  1. TabPFN/RandomForest (CPU)      │
│     Predict cash crunch risk        │
│                                     │
│  2. PII Redactor (CPU)              │
│     Strip client names, emails      │
│                                     │
│  4. PII Rehydrator (CPU)            │
│     Restore real names in output    │
│                                     │
│  Data: invoices.csv, monthly.csv   │
└──────────────────┬──────────────────┘
                   │
        Cloudflare Tunnel (TLS 1.3)
        [No PII crosses this boundary]
                   │
┌──────────────────▼──────────────────┐
│  Google Colab (Ephemeral GPU)       │
│                                     │
│  3. Gemma LLM (T4 GPU)              │
│     Generate action plan & emails   │
│     Never sees client names         │
│                                     │
└─────────────────────────────────────┘
```

## The 4-Node Workflow

### Node 1: Local TabPFN Forecast
**Purpose:** Predict cashflow crunch probability based on historical data

**Input:**
- `monthly_history.csv`: 16+ months of expenses, invoices, late-payment rates
- User inputs: upcoming expenses, expected invoices

**Process:**
1. Load historical data from CSV
2. Train TabPFN classifier on local CPU (with RandomForest fallback)
3. Generate two scenarios:
   - **Baseline**: Current cashflow without collecting overdue invoices
   - **Recovered**: Cashflow after collecting top overdue invoice (+$1,450)

**Output:**
```python
{
  "engine": "TabPFN-v2 (Local CPU)",
  "avg_late_ratio": 0.24,
  "prob_baseline": 0.75,  # 75% chance of cash crunch
  "prob_recovered": 0.15,  # 15% chance after collecting one invoice
}
```

**Why Local?**
- No internet needed; instant inference
- No PII leaves your PC
- Direct access to sensitive monthly data

---

### Node 2: Local PII Redactor
**Purpose:** Strip all identifiable client information before sending to remote AI

**Input:**
- `invoices.csv`: Real client names, emails, projects, amounts, due dates

**Process:**
1. Parse invoices.csv
2. Identify overdue invoices
3. Replace client identifiers with tokens:
   - `BlueWave Health Media` → `[CLIENT_INV-104]`
   - `ap@bluewavehealth.org` → (omitted entirely)
   - `Dashboard Redesign` → (omitted entirely)

**Output:**
```text
ANONYMIZED OVERDUE LEDGER (Total Overdue: USD 3,550 across 2 invoices):
- Invoice ID: INV-104 | Client Token: [CLIENT_INV-104] | Amount: USD 1,450.00 | Days Overdue: 39
- Invoice ID: INV-101 | Client Token: [CLIENT_INV-101] | Amount: USD 2,100.00 | Days Overdue: 25
```

**Why Local?**
- Client names are your competitive advantage and NDA obligation
- Redaction happens in-memory; never logged or cached
- You control what leaves your PC

---

### Node 3: Remote Gemma Inference
**Purpose:** Use a powerful LLM on Colab's free GPU to generate strategic recommendations

**Input:**
- TabPFN forecast (anonymized numbers)
- Redacted ledger (no client names, just tokens)

**Process:**
1. Send encrypted payload through Cloudflare tunnel to Colab GPU
2. Gemma model reads:
   - "75% cash crunch risk vs. 15% if INV-104 is collected"
   - "Highest-priority anonymous invoices: [CLIENT_INV-104], [CLIENT_INV-101], ..."
3. Generates three sections:
   - **Risk Assessment**: Plain-English explanation of cashflow threat
   - **Prioritized Queue**: Ranking of which invoices to chase first (using tokens)
   - **Email Template**: Polite payment reminder draft (addressing `[CLIENT_INV-104]`)

**Output:**
```markdown
### 1. TabPFN Cashflow Risk Assessment
Your baseline risk is 75%. Collecting INV-104 drops this to 15%.

### 2. Prioritized Collection Queue
1. [CLIENT_INV-104] — INV-104 ($1,450, 39 days)
2. [CLIENT_INV-101] — INV-101 ($2,100, 25 days)

### 3. Ready-to-Send Email
Dear [CLIENT_INV-104],

I hope this email finds you well...
```

**Why Remote?**
- Colab's T4 GPU is free
- Gemma is fast and capable for this task
- You avoid paying for API credits (ChatGPT, Claude, etc.)
- Data is encrypted in-transit (Cloudflare tunnels use TLS 1.3)

---

### Node 4: Local PII Rehydrator
**Purpose:** Restore real client information to the Gemma output on your PC

**Input:**
- Gemma's response with anonymized tokens (e.g., `[CLIENT_INV-104]`)
- Original `invoices.csv` with real client data

**Process:**
1. Parse Gemma's response
2. For each token `[CLIENT_INV-104]`:
   - Look up INV-104 in invoices.csv
   - Find client name: `BlueWave Health Media`
   - Find email: `ap@bluewavehealth.org`
   - Find project: `Dashboard Redesign`
3. Replace `[CLIENT_INV-104]` with:
   ```
   **BlueWave Health Media** (`ap@bluewavehealth.org` — *Dashboard Redesign*)
   ```

**Output:**
```markdown
### 1. TabPFN Cashflow Risk Assessment
Your baseline risk is 75%. Collecting INV-104 drops this to 15%.

### 2. Prioritized Collection Queue
1. **BlueWave Health Media** (`ap@bluewavehealth.org` — *Dashboard Redesign*) — INV-104 ($1,450, 39 days)
2. **Acme Corp** (`billing@acme.com` — *Mobile App*) — INV-101 ($2,100, 25 days)

### 3. Ready-to-Send Email
Dear **BlueWave Health Media**,

I hope this email finds you well...
```

**Why Local?**
- Rehydration is pure text substitution (regex)
- Instant, no network delay
- Sensitive data restored only on your PC

---

## Error Handling & Resilience

### Retry Logic for Colab Timeouts
If Gemma inference fails (Colab tunnel down, GPU OOM):
- **Attempt 1**: Try immediately
- **Attempt 2**: Wait 2s, retry
- **Attempt 3**: Wait 4s, retry
- **Fail**: Return error with actionable message ("Check if your Colab notebook is still running")

### TabPFN Fallback
If TabPFN library fails to load:
- Fall back to scikit-learn's RandomForestClassifier
- Same API, same output format
- No user action needed; logged as "Fallback (Local CPU)"

### Input Validation
- Reject negative expenses or invoices
- Skip CSV rows with invalid amounts or dates
- Warn if no overdue invoices exist (graceful empty state)

### CSV Robustness
- Validate required columns exist
- Skip malformed rows instead of crashing
- Log warnings for debugging

---

## Data Flow Diagram

```
┌─ User Interface (Streamlit) ─────────────────────────────────────────┐
│                                                                      │
│  [Upcoming Expenses] [Expected Invoices] → Run Agent Button          │
│                                                                      │
└────────────────────────────┬─────────────────────────────────────────┘
                             │
                    build_cashflow_graph()
                    (LangGraph StateGraph)
                             │
         ┌───────────────────┼───────────────────┐
         │                   │                   │
    ┌────▼─────┐        ┌────▼─────┐        ┌───▼──────┐
    │ Node 1    │        │ Node 2    │        │ Node 3   │
    │ TabPFN    │──────► │ Redactor  │──────► │ Gemma    │
    │ Forecast  │        │ (Local)   │        │ (Colab)  │
    └──────────┘        └───────────┘        └──┬───────┘
         ▲                                       │
         │                                       │
    monthly_history.csv                    Cloudflare
         │                                    Tunnel
    invoices.csv                               │
                                          ┌────▼────┐
                                          │ Node 4   │
                                          │ Rehydra- │
                                          │ tor      │
                                          └────┬────┘
                                               │
                                    final_output
                                    (display in UI)
```

---

## Security Model

### PII Boundaries

| Data | Location | Encrypted? | Visible? |
|------|----------|-----------|----------|
| Client names, emails | invoices.csv (local) | At-rest | Only on your screen |
| Expenses, invoices | monthly_history.csv (local) | At-rest | Only on your screen |
| TabPFN numbers | Tunnel + Colab | In-transit (TLS 1.3) | Colab sees probabilities |
| Anonymized ledger | Tunnel + Colab | In-transit (TLS 1.3) | Colab sees tokens only |
| Gemma response | Tunnel (return) | In-transit (TLS 1.3) | Sent back as tokens |
| Rehydrated output | Local PC | At-rest | Only on your screen |

### Threat Model

**Attack Scenario 1: Intercept Cloudflare Tunnel**
- **Risk**: Low (TLS 1.3 encrypted)
- **Impact**: Attacker sees anonymized numbers, not client names
- **Mitigation**: Cloudflare tunnel uses military-grade encryption

**Attack Scenario 2: Compromise Colab GPU**
- **Risk**: Low (ephemeral, shared infrastructure)
- **Impact**: Attacker never sees client names (PII not transmitted)
- **Mitigation**: PII redaction happens locally before transmission

**Attack Scenario 3: Lose invoices.csv**
- **Risk**: High (local file loss)
- **Impact**: Client data exposure
- **Mitigation**: Back up invoices.csv to encrypted cloud storage

---

## File Dependencies

```
app.py
├── agent.py (core orchestration)
│   ├── TabPFN/RandomForest (compute_tabpfn_probabilities)
│   ├── PII redaction (get_redacted_invoice_payload)
│   ├── PII rehydration (rehydrate_pii_locally)
│   ├── Gemma inference (node_gemma_reasoning)
│   └── LangGraph graph builder (build_cashflow_graph)
├── features.py (new features)
│   ├── Email templates (generate_email_templates)
│   ├── Multi-month forecasts (forecast_multi_month)
│   ├── CSV export (export_to_csv)
│   └── Summary reports (generate_summary_report)
├── seed_data.py (sample data generation)
├── invoices.csv (runtime data)
└── monthly_history.csv (runtime data)

colab_gpu_server.ipynb
├── Ollama installation
├── Gemma model download
└── Cloudflare tunnel setup
```

---

## Performance Characteristics

| Component | Latency | CPU/GPU | Notes |
|-----------|---------|--------|-------|
| TabPFN fit + predict | ~0.5s | CPU | Fast ML for tabular data |
| PII redaction | ~10ms | CPU | Regex substitution |
| Cloudflare tunnel | ~100-500ms | Network | Depends on ISP & Colab region |
| Gemma inference | ~5-15s | GPU (T4) | Token streaming |
| PII rehydration | ~50ms | CPU | Regex substitution |
| **Total E2E** | **~10-20s** | Hybrid | Local + remote orchestration |

---

## Future Enhancements

- [ ] Multi-currency support (USD, EUR, GBP, etc.)
- [ ] Invoice template generator
- [ ] Automated SMTP email sending
- [ ] Historical trend charts
- [ ] Multi-tenant org separation
- [ ] Mobile app (React Native)
- [ ] Stripe/Wave/Xero API integration
- [ ] Bulk invoice upload from PDF
- [ ] Collaboration features (share dashboards with accountants)
