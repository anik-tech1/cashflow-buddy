# Contributing to CashflowBuddy

Thanks for considering a contribution! This guide will help you get started.

## Code of Conduct

Be respectful, inclusive, and assume good intent. Report violations to [maintainer email].

## Getting Started

### 1. Fork & Clone
```bash
git clone https://github.com/yourusername/cashflow-buddy.git
cd cashflow-buddy
git remote add upstream https://github.com/aniket/cashflow-buddy.git
```

### 2. Set Up Dev Environment
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install pytest pytest-cov black flake8 mypy
```

### 3. Create a Feature Branch
```bash
git checkout -b feature/your-feature-name
```

## What We're Looking For

### High Priority
- **Error Handling** – Retry logic for Colab timeouts, graceful fallbacks for missing models
- **Input Validation** – Sanitize CSV inputs, prevent negative expenses/invoices
- **PII Edge Cases** – Handle special characters, accented names, emoji in client redaction
- **Unit Tests** – Cover TabPFN fallback, redaction logic, graph workflow
- **Documentation** – Architecture diagrams, setup guides, inline comments

### Medium Priority
- **Feature Additions**
  - Invoice template generator
  - Multi-month trend forecasts
  - CSV/PDF export
  - SMTP email automation
  - Multi-currency support
- **UI/UX Improvements** – Progress indicators per graph node, better error messages
- **Performance** – Caching for repeated TabPFN queries, async LLM calls

### Lower Priority
- **Deployment** – Docker, Railway, Vercel configs
- **Analytics** – Inference latency tracking, scenario usage logs
- **Extras** – Mobile app, mobile app, Stripe/Wave integrations

## Code Style

- **Format** – Use `black` (line length 100)
- **Lint** – Pass `flake8` (exclude `.venv, __pycache__`)
- **Type Hints** – Use `mypy` for static analysis
- **No Comments** – Code should be self-documenting; add docstrings only if unclear

```bash
black .
flake8 . --exclude .venv,__pycache__
mypy . --ignore-missing-imports
```

## Testing

Write tests for new features or bug fixes. Use `pytest`.

```bash
pytest tests/
pytest tests/ --cov=. --cov-report=html
```

Test structure:
```
tests/
  test_agent.py          # TabPFN, redaction, rehydration, graph
  test_app.py            # Streamlit UI integration (if applicable)
  test_seed_data.py      # CSV generation
  test_edge_cases.py     # PII edge cases, negative inputs, malformed CSVs
```

## Commit Message Format

```
<type>: <subject>

<body (optional)>

<footer (optional)>
```

Types: `feat`, `fix`, `docs`, `test`, `refactor`, `perf`, `chore`

Examples:
```
feat: add retry logic for Colab tunnel timeouts

Implement exponential backoff (3 retries, 2s → 4s → 8s) when Colab
tunnel is unreachable. Falls back to RandomForest if TabPFN unavailable.

Fixes #42
```

```
fix: handle special characters in PII rehydration

Escape regex special chars in client names (e.g., "A&B Inc." → "A\\&B Inc.")
before substituting tokens back into LLM output.

Fixes #38
```

## Pull Request Process

1. **Before submitting:**
   - Run `black .`, `flake8`, `mypy`
   - Run `pytest` and ensure all tests pass
   - Update `README.md` if behavior changes
   - Add tests for new features

2. **Open a PR against `main`:**
   - Reference issue(s): "Fixes #123"
   - Describe what changed and why
   - Include any breaking changes

3. **Wait for review:**
   - Maintainers will provide feedback
   - Update based on suggestions
   - Rebase if needed

4. **Merge:**
   - Squash commits if appropriate
   - Maintainer will merge once approved

## Architecture Notes

### The Split-Brain Flow

```
Local CPU:
  invoices.csv + monthly_history.csv
  ↓
  1. TabPFN Forecast (or RandomForest fallback)
  2. PII Redactor (strip names, emails, projects)
  ↓
  [redacted JSON] ──(Cloudflare tunnel)──→ Colab GPU
                                          ↓
                                  3. Gemma LLM
                                  (writes strategy)
  ↓
  [anonymized response] ←(Cloudflare tunnel)─
  ↓
  4. Local Rehydrator (restore client names)
  ↓
  final_output (ready to use)
```

**Key Principle:** Never let PII cross the network boundary.

### Key Functions

- `compute_tabpfn_probabilities()` – Runs TabPFN/RandomForest on local CPU
- `get_redacted_invoice_payload()` – Strips PII locally
- `rehydrate_pii_locally()` – Restores PII after LLM response
- `build_cashflow_graph()` – Orchestrates the 4-node workflow with LangGraph

## Debugging Tips

- **Colab Tunnel Not Connecting?**
  ```bash
  curl -v https://<your-tunnel-url>/api/tags
  ```
  If it fails, check that `colab_gpu_server.ipynb` is still running.

- **TabPFN Not Installed?**
  The code falls back to RandomForest automatically. Check logs to confirm.

- **PII Not Rehydrating?**
  Enable debug logging in `agent.py` to see token-to-name mappings.

- **Streamlit Not Reloading?**
  Streamlit caches by default. Use `--logger.level=debug` to trace caching.

## Release Process

Maintainers only:
1. Update `__version__` in `__init__.py`
2. Update `CHANGELOG.md`
3. Tag: `git tag v1.0.0`
4. Push: `git push origin main --tags`
5. Create GitHub Release

## Questions?

- Open an issue on GitHub
- Check `ARCHITECTURE.md` for deep dives
- See `README.md` for quick start

Thanks for contributing! 🎉
