# Deploy CashflowBuddy to Render - Step-by-Step

Your GitHub repo is ready: https://github.com/anik-tech1/cashflow-buddy

## ⚡ Quick Deploy (5 minutes)

### Step 1: Go to Render Dashboard
https://dashboard.render.com

### Step 2: Click "New +" → "Web Service"

### Step 3: Connect GitHub
- Click **"Connect a repository"**
- Search for `cashflow-buddy`
- Click **"Connect"**

### Step 4: Configure Service

Fill in these fields:
```
Name:              cashflow-buddy
Environment:       Python 3
Build Command:     pip install -r requirements.txt
Start Command:     streamlit run app.py --server.port=10000 --server.address=0.0.0.0
Plan:              Free (or Starter for $7/mo for always-on)
```

Render auto-detects `render.yaml` from your repo.

### Step 5: Add Environment Variables

**After deployment starts**, go to **Settings** → **Environment** → **Add Environment Variable**

Add this critical variable:
```
Key:   COLAB_TUNNEL_URL
Value: https://your-tunnel-url.trycloudflare.com
```

⚠️ **Get this from your Colab notebook** (`colab_gpu_server.ipynb`)

### Step 6: Click "Create Web Service"

Render deploys automatically. Wait ~2-3 minutes.

Your live URL: `https://cashflow-buddy.onrender.com`

---

## 🔑 Before You Deploy - Checklist

- [ ] GitHub repo pushed: https://github.com/anik-tech1/cashflow-buddy ✅
- [ ] `render.yaml` in repo root ✅
- [ ] `.streamlit/config.toml` in repo ✅
- [ ] `requirements.txt` has all dependencies ✅
- [ ] You have Colab tunnel URL ready (from notebook)
- [ ] Colab notebook (`colab_gpu_server.ipynb`) is running

---

## 🚀 Deploy Now

1. Open https://dashboard.render.com (sign up if needed)
2. Click **New +** → **Web Service**
3. Select your `cashflow-buddy` GitHub repo
4. Fill in the 4 fields above
5. Click **Create Web Service**
6. Wait for deployment ✅
7. Go to **Settings** → **Environment** and add `COLAB_TUNNEL_URL`
8. Your app is live!

---

## 📱 Access Your App

- **Public URL**: `https://cashflow-buddy.onrender.com`
- **Status Page**: `https://dashboard.render.com` (in your services list)

---

## 🔄 Auto-Redeploy on Git Push

Every time you push to GitHub:
```bash
git add .
git commit -m "Update feature"
git push origin main
```

Render automatically redeploys within 1-2 minutes. No manual action needed.

---

## ⚠️ Important Notes

### Colab Tunnel Expires Every ~8 Hours
1. Restart `colab_gpu_server.ipynb` in Colab
2. Copy new tunnel URL
3. Update `COLAB_TUNNEL_URL` in Render Settings
4. Restart service (click the restart button in Render dashboard)

### Free Tier Limitations
- **Spins down** after 15 minutes of inactivity
- First request after spindown takes ~30 seconds
- For production, upgrade to **Starter** ($7/month) or higher

### If App Won't Start
1. Check Render logs (Dashboard → Service → Logs)
2. Look for Python errors or missing dependencies
3. Verify `requirements.txt` has all packages
4. Common issue: Missing `COLAB_TUNNEL_URL` environment variable

---

## 📊 Monitor Your App

In Render Dashboard:
- **Logs**: Real-time output (look for connection errors)
- **Metrics**: CPU/memory usage
- **Events**: Deployment history

---

## 💰 Pricing

| Tier | Cost | Best For |
|------|------|----------|
| Free | $0 | Dev/demos (spins down) |
| Starter | $7/mo | Personal use (always on) |
| Standard | $25/mo | Production (auto-scaling) |

---

## 🆘 Troubleshooting

### "Cannot connect to Colab GPU"
→ Check `COLAB_TUNNEL_URL` is set in Render Environment  
→ Make sure notebook is still running  
→ Tunnel URLs expire; restart notebook if older than 8 hours

### "App won't load"
→ Check Render logs for Python errors  
→ Verify all dependencies in `requirements.txt`  
→ Free tier may be spinning down; refresh page

### "Port already in use"
→ This shouldn't happen on Render (it assigns ports)  
→ Check `render.yaml` has `port: 10000`

---

## ✅ You're Ready!

Your CashflowBuddy is production-ready with:
- ✅ Split-brain privacy architecture
- ✅ TabPFN + Gemma AI orchestration
- ✅ Email templates, forecasts, CSV export
- ✅ Comprehensive error handling & tests
- ✅ Full documentation
- ✅ One-click Render deployment

**Next step:** Deploy now at https://dashboard.render.com
