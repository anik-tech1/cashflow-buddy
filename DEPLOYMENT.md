# CashflowBuddy Deployment Guide

## Local Development

### Prerequisites
- Python 3.9+
- Google Colab account (free T4 GPU)

### Quick Start
```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

Visit `http://localhost:8501`.

## Docker Deployment

### Build & Run Locally
```bash
docker build -t cashflow-buddy .
docker run -p 8501:8501 cashflow-buddy
```

Visit `http://localhost:8501`.

### Environment Variables
```bash
docker run -p 8501:8501 \
  -e COLAB_TUNNEL_URL=https://random-words.trycloudflare.com \
  cashflow-buddy
```

## Cloud Deployment

### Railway
```bash
railway login
railway init
railway up
```

Add these environment variables in Railway dashboard:
- `COLAB_TUNNEL_URL`: Your Cloudflare tunnel URL

### Vercel (Streamlit Community Cloud)
1. Push repo to GitHub
2. Visit https://share.streamlit.io
3. Select your repo
4. Set `COLAB_TUNNEL_URL` in Secrets

### Google Cloud Run
```bash
gcloud run deploy cashflow-buddy \
  --source . \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars COLAB_TUNNEL_URL=<your-tunnel-url>
```

## Production Notes

- **PII Handling**: Client data never leaves your PC unencrypted
- **Colab Tunnel Lifetime**: Tunnels stay active for ~8 hours; restart as needed
- **CSV Backups**: Store `invoices.csv` and `monthly_history.csv` securely
- **Logging**: Check container logs for connection issues

## Troubleshooting

**Port 8501 already in use:**
```bash
streamlit run app.py --server.port 8502
```

**Colab tunnel unreachable:**
- Restart the Colab notebook
- Verify tunnel URL is correct
- Check firewall rules

**CSV parsing errors:**
- Ensure CSV headers match: `invoice_id`, `client_name`, `contact_email`, `project_name`, `amount`, `status`, `days_overdue`
- Run `python seed_data.py` to regenerate sample data
