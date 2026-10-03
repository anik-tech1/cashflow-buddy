# Deploy CashflowBuddy to Render

Render is a modern cloud platform that makes deploying Streamlit apps simple. Here's how to get CashflowBuddy running on Render in 5 minutes.

## Prerequisites

1. GitHub repository with CashflowBuddy code pushed
2. Render account (free tier available at https://render.com)
3. Your Colab tunnel URL (from `colab_gpu_server.ipynb`)

## Step 1: Create `render.yaml` (Infrastructure as Code)

Add this file to your repo root:

```yaml
services:
  - type: web
    name: cashflow-buddy
    env: python
    plan: free
    buildCommand: pip install -r requirements.txt
    startCommand: streamlit run app.py --server.port=10000 --server.address=0.0.0.0
    envVars:
      - key: STREAMLIT_SERVER_HEADLESS
        value: true
      - key: STREAMLIT_SERVER_PORT
        value: 10000
      - key: STREAMLIT_SERVER_ADDRESS
        value: 0.0.0.0
```

## Step 2: Create `.streamlit/config.toml`

Create this directory structure and file:

```toml
[server]
port = 10000
headless = true
address = "0.0.0.0"

[browser]
gatherUsageStats = false

[logger]
level = "info"
```

## Step 3: Push to GitHub

```bash
git add render.yaml .streamlit/config.toml
git commit -m "Add Render deployment config"
git push origin main
```

## Step 4: Deploy on Render Dashboard

1. Go to https://dashboard.render.com
2. Click **New +** → **Web Service**
3. Select **Connect a repository** → choose your GitHub repo
4. Fill in:
   - **Name**: `cashflow-buddy`
   - **Environment**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `streamlit run app.py --server.port=10000 --server.address=0.0.0.0`
   - **Plan**: Free (or Pro for better performance)

5. Click **Create Web Service**

## Step 5: Add Environment Variables

After deployment starts, go to **Settings** → **Environment**:

Add these variables:

| Key | Value |
|-----|-------|
| `COLAB_TUNNEL_URL` | `https://your-tunnel-url.trycloudflare.com` |
| `STREAMLIT_SERVER_HEADLESS` | `true` |
| `STREAMLIT_SERVER_PORT` | `10000` |

**Important:** Replace with your actual Colab tunnel URL from the notebook.

## Step 6: View Live App

Once deployed, Render gives you a public URL like:
```
https://cashflow-buddy.onrender.com
```

Your app is now live!

## Troubleshooting

### App won't start
```bash
# Check Render logs in dashboard
# If you see Python errors, check requirements.txt is installed
```

### "Cannot connect to Colab"
- Verify `COLAB_TUNNEL_URL` is set correctly in Render Environment
- Ensure Colab notebook is still running
- Colab tunnels expire after ~8 hours; restart the notebook when needed

### Free tier limitations
- Render free tier spins down after 15 minutes of inactivity
- First request after spindown takes ~30s to start
- For production, upgrade to **Starter** ($7/month) or **Standard** plan

### Port binding error
- Render automatically assigns port 10000
- Don't hardcode ports in code; use the config above

## Auto-Redeploy on Git Push

Render auto-deploys whenever you push to your GitHub repo:

```bash
git add features.py
git commit -m "Add new feature"
git push origin main
# Render automatically redeploys within 1-2 minutes
```

## Update Colab Tunnel URL

When your tunnel expires (every ~8 hours):

1. Restart `colab_gpu_server.ipynb`
2. Copy new tunnel URL
3. In Render dashboard → **Settings** → **Environment** → Update `COLAB_TUNNEL_URL`
4. Restart app via **Manual Deploy**

Or automate with environment variables:

```bash
# Set via Render CLI (if installed)
render env set COLAB_TUNNEL_URL "https://new-tunnel-url.trycloudflare.com"
```

## Production Tips

### Use Persistent Environment Variables
Instead of hardcoding tunnel URLs, use Render Secrets:
- **Settings** → **Environment** → Add as `Secret` (encrypted)
- Access in code: `os.getenv("COLAB_TUNNEL_URL")`

### Monitor Performance
- Render dashboard shows memory/CPU usage
- Free tier = 0.5 CPU + 512MB RAM (usually sufficient for Streamlit)
- Upgrade if hitting limits

### Custom Domain
- Go to **Settings** → **Custom Domain**
- Point your domain DNS to Render
- Free HTTPS certificate included

## Alternative: Deploy via Render CLI

```bash
# Install Render CLI
npm install -g @render-com/cli

# Login
render login

# Deploy from command line
render deploy --repo https://github.com/yourusername/cashflow-buddy
```

## Cost Breakdown

| Tier | Price | Use Case |
|------|-------|----------|
| Free | $0 | Development, demos (spins down after 15 min) |
| Starter | $7/month | Personal use (always on) |
| Standard | $25/month | Production (auto-scaling) |

## Quick Deploy Button (Optional)

Add this to your README.md for one-click deploys:

```markdown
[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/yourusername/cashflow-buddy)
```

Then create `render.yaml` at repo root (already done above).

## Monitoring & Logs

View real-time logs:
1. **Dashboard** → Select service → **Logs**
2. Or use Render CLI: `render logs cashflow-buddy --tail`

Check for:
- Streamlit startup messages
- Colab connection errors
- CSV parsing warnings

## Next Steps

1. ✅ Push code to GitHub
2. ✅ Create Render account
3. ✅ Deploy web service
4. ✅ Set `COLAB_TUNNEL_URL` environment variable
5. ✅ Test with real data

Your app is now live and auto-updates on every GitHub push!
