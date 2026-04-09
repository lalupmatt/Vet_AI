# Vet AI - Deployment Guide

Your Flask/React veterinary AI application is ready for production deployment. Choose your preferred platform below.

---

## 🚀 Quick Start Options

### Option 1: Deploy on Render (Recommended - Easiest)

**Step 1: Prepare Your Repository**
```bash
git init
git add .
git commit -m "Initial commit: Vet AI deployment"
git push origin main  # Push to GitHub/GitLab
```

**Step 2: Connect to Render**
1. Go to [render.com](https://render.com)
2. Click "New +" → "Web Service"
3. Connect your GitHub repository
4. Configure:
   - **Name:** vet-ai-app
   - **Runtime:** Docker
   - **Build Command:** `docker build .`
   - **Start Command:** Auto-detected from Dockerfile

**Step 3: Add Environment Variables**
1. In Render dashboard, go to Environment
2. Add the following:
   ```
   OPENROUTER_API_KEY=sk-or-v1-your-actual-key-here
   SECRET_KEY=generate-a-random-secret-key
   FLASK_ENV=production
   ```

**Step 4: Deploy**
- Click "Create Web Service"
- Render builds and deploys automatically
- Your app is live at `https://vet-ai-app.onrender.com`

---

### Option 2: Deploy on Railway.app (Fast Alternative)

**Step 1: Push to Git**
```bash
git init && git add . && git commit -m "Deploy ready"
git push origin main
```

**Step 2: Connect Railway**
1. Go to [railway.app](https://railway.app)
2. Click "New Project" → "Deploy from GitHub"
3. Select your repository
4. Railway auto-detects Dockerfile and deploys

**Step 3: Add Variables**
- In Railway dashboard → Variables
- Add `OPENROUTER_API_KEY` and `SECRET_KEY`

**Step 4: Deploy**
- Railway deploys automatically
- Live at your Railway domain

---

### Option 3: Deploy on Heroku (Classic)

**Step 1: Install Heroku CLI**
```bash
# macOS/Linux
curl https://cli.heroku.com/install.sh | sh

# Windows: Download from https://devcenter.heroku.com/articles/heroku-cli
```

**Step 2: Create & Deploy**
```bash
heroku login
heroku create vet-ai-app
heroku config:set OPENROUTER_API_KEY=sk-or-v1-your-key-here
heroku config:set SECRET_KEY=$(openssl rand -hex 16)
git push heroku main
```

**Step 3: View Logs**
```bash
heroku logs --tail
```

---

### Option 4: Deploy on Docker Hub + VPS

**Step 1: Build & Push Docker Image**
```bash
docker build -t yourusername/vet-ai:latest .
docker push yourusername/vet-ai:latest
```

**Step 2: On Your VPS (DigitalOcean, Linode, AWS EC2)**
```bash
docker pull yourusername/vet-ai:latest
docker run -d \
  -p 5000:5000 \
  -e OPENROUTER_API_KEY=sk-or-v1-your-key \
  -v /data/uploads:/app/static/uploads \
  -v /data/animals.json:/app/animals.json \
  -v /data/users.json:/app/users.json \
  --restart unless-stopped \
  --name vet-ai \
  yourusername/vet-ai:latest
```

---

## 📋 Pre-Deployment Checklist

- [ ] Update `.env` with real `OPENROUTER_API_KEY`
- [ ] Generate secure `SECRET_KEY` for production
- [ ] Test app locally: `python app.py` or `docker-compose up`
- [ ] Verify all JSON files (users.json, animals.json) have proper data
- [ ] Check dataset folder has animal images
- [ ] Review app.py for any hardcoded values to change
- [ ] Set `FLASK_DEBUG=False` in production

---

## 🔒 Security Hardening

### 1. Update Secret Key
Generate a secure key:
```python
import secrets
print(secrets.token_urlsafe(32))
```
Add to `.env`:
```
SECRET_KEY=your-generated-key-here
```

### 2. Protect Sensitive Data
- **Never commit `.env` file** - it's in `.gitignore`
- Use `.env.example` for template
- Store all API keys in platform environment variables

### 3. HTTPS Only
- All production platforms (Render, Railway, Heroku) auto-enable HTTPS
- Update app.py if needed:
  ```python
  SESSION_COOKIE_SECURE = True
  SESSION_COOKIE_HTTPONLY = True
  ```

### 4. Rate Limiting (Optional)
Add to app.py:
```python
from flask_limiter import Limiter
limiter = Limiter(app, key_func=lambda: session.get('user_id'))

@app.route('/chat', methods=['POST'])
@limiter.limit("10 per minute")
def chat():
    # ... existing code
```

---

## 📊 Monitoring & Logs

### Render/Railway/Heroku
- Built-in log viewing in dashboard
- Set up alerts for errors

### Custom Monitoring
Add error tracking:
```python
import logging
logging.basicConfig(level=logging.INFO)
```

---

## 🛠️ Troubleshooting

**Issue: "No module named 'cv2'"**
- Solution: Dockerfile includes OpenCV installation ✓

**Issue: "OPENROUTER_API_KEY not set"**
- Solution: Add environment variable to your platform

**Issue: Images not persisting**
- Solution: Mount volumes for `/app/static/uploads` and `/app/dataset`

**Issue: Upload fails**
- Solution: Check `MAX_CONTENT_LENGTH=16MB` in production.py

---

## 📈 Performance Tips

1. **Cache animal dataset** in memory after first load
2. **Optimize image matching** - consider pre-computing features
3. **Use CDN** for static files (CSS, images)
4. **Enable compression** in Gunicorn:
   ```
   gunicorn --bind 0.0.0.0:5000 --workers 4 --compress app:app
   ```

---

## 🔄 Continuous Deployment

### Auto-Deploy on Git Push (Render/Railway)
1. Connect your GitHub repo
2. Set branch to `main` or `master`
3. Every push automatically deploys

### With GitHub Actions
Create `.github/workflows/deploy.yml`:
```yaml
name: Deploy
on:
  push:
    branches: [main]
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: akhileshns/heroku-deploy@v3.13.15
        with:
          heroku_api_key: ${{secrets.HEROKU_API_KEY}}
          heroku_app_name: vet-ai-app
          heroku_email: your-email@example.com
```

---

## 💾 Database Migration

Currently using JSON files. To migrate to PostgreSQL later:

1. Create Supabase project (free tier available)
2. Update app.py to use `psycopg2` instead of JSON
3. Create migration script for existing data
4. Update environment variables

---

## 📞 Support

- **Render Issues:** https://render.com/docs
- **Railway Issues:** https://docs.railway.app
- **Heroku Issues:** https://devcenter.heroku.com
- **Flask Issues:** https://flask.palletsprojects.com

---

## Next Steps After Deployment

1. ✅ Test login page in production
2. ✅ Upload sample animal images
3. ✅ Test AI chat functionality
4. ✅ Verify health reports generate correctly
5. ✅ Set up monitoring/alerts
6. ✅ Create backup strategy for JSON files
