# ⚡ Vet AI - Quick Deploy (5 Minutes)

Choose your platform and follow these simple steps.

## 🎯 Fastest Option: Render.com (Recommended)

### Step 1: Push Code to GitHub
```bash
cd vet-ai-app
git init
git add .
git commit -m "Deploy Vet AI"
git push origin main
```

### Step 2: Deploy on Render
1. Go to https://render.com (create free account)
2. Click **"New +" → "Web Service"**
3. Click **"Connect account"** to link GitHub
4. Select your `vet-ai-app` repository
5. Configure:
   - **Name:** `vet-ai-app`
   - **Runtime:** Docker (auto-detected)
   - **Branch:** main
   - **Auto-deploy:** ✓ ON

### Step 3: Add Environment Variables
1. Scroll down to **"Environment"**
2. Add these variables:
   ```
   OPENROUTER_API_KEY = sk-or-v1-your-actual-key-here
   SECRET_KEY = generate-random-32-chars
   FLASK_ENV = production
   ```

### Step 4: Deploy
Click **"Create Web Service"** and wait 2-3 minutes. Your app is live!

**Your URL:** `https://vet-ai-app.onrender.com`

---

## 🚂 Alternative: Railway.app

1. Go to https://railway.app
2. Click **"New Project"** → **"Deploy from GitHub"**
3. Select your repository
4. Add environment variables (same as above)
5. Deploy — done!

---

## 🔧 Local Testing First (Optional)

```bash
cd vet-ai-app

# Install dependencies
pip install -r requirements.txt

# Set environment
cp .env.example .env
# Edit .env - add your OPENROUTER_API_KEY

# Run locally
python app.py
# Opens on http://localhost:5000
```

**Login with:**
- Admin: `admin` / `admin123`
- Farmer: `farmer1` / `farmer123`

---

## 🐳 Deploy with Docker (On Your VPS)

```bash
# Build
docker build -t vet-ai .

# Run
docker run -d \
  -p 5000:5000 \
  -e OPENROUTER_API_KEY=sk-or-v1-your-key \
  --name vet-ai \
  --restart unless-stopped \
  vet-ai

# View logs
docker logs -f vet-ai
```

---

## 🔐 Security Checklist

- [ ] Changed default passwords in `users.json`
- [ ] Generated new `SECRET_KEY`
- [ ] Added `OPENROUTER_API_KEY` to environment variables
- [ ] Using HTTPS (auto on Render/Railway)
- [ ] Backed up `animals.json` and `users.json`

---

## ✅ After Deployment

1. Test login page works
2. Try uploading an animal image
3. Verify AI chat responds
4. Check health reports generate

---

## 📞 Troubleshooting

**"Module not found" error?**
- Check requirements.txt has all dependencies
- Render/Railway auto-installs from requirements.txt

**"OPENROUTER_API_KEY not set"?**
- Add it to platform's environment variables
- Restart the app after adding

**Images not persisting?**
- Use Render's persistent volumes feature
- Mount `/app/static` and `/app/dataset` folders

**Slow responses?**
- OpenRouter API takes 5-15 seconds normally
- Check internet connection
- Verify API key quota

---

## 🎓 Full Documentation

See `DEPLOYMENT_GUIDE.md` for:
- Advanced configuration
- Performance optimization
- CI/CD setup
- Database migration

---

**That's it! 🎉 Your Vet AI app is now live!**
