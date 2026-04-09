# 🐾 Vet AI - Veterinary Intelligence Assistant

An AI-powered veterinary diagnostic platform featuring pet health analysis, image recognition for animal identification, and intelligent chat-based medical advice.

## ✨ Features

- **🔐 Role-Based Access**: Separate admin and user dashboards
- **📸 Image Recognition**: Identify animals and match to health records using computer vision
- **🤖 AI Diagnosis**: Get instant health analysis using OpenRouter AI
- **💬 Smart Chat**: Ask veterinary questions with pet context awareness
- **📋 Pet Profiles**: Manage complete animal health records with vaccination history
- **📊 Health Reports**: Automated health scoring and care recommendations
- **🏥 Emergency Alerts**: Risk-level indicators for urgent conditions

## 🛠️ Tech Stack

- **Backend**: Flask (Python 3.11)
- **Frontend**: HTML5, CSS3, Vanilla JavaScript
- **Image Processing**: OpenCV, NumPy
- **AI**: OpenRouter API (LLaMA 3)
- **Deployment**: Docker, Gunicorn

## 📦 Installation

### Local Development

```bash
# Clone or extract the project
cd vet-ai-app

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env and add your OPENROUTER_API_KEY

# Run the app
python app.py
```

App runs on `http://localhost:5000`

### Docker

```bash
# Build image
docker build -t vet-ai .

# Run container
docker run -p 5000:5000 \
  -e OPENROUTER_API_KEY=your-key-here \
  -v $(pwd)/static:/app/static \
  vet-ai
```

### Docker Compose

```bash
cp .env.example .env
# Edit .env with your API key

docker-compose up -d
```

## 🔑 API Keys Required

### OpenRouter API
1. Sign up at [https://openrouter.ai](https://openrouter.ai)
2. Get your API key from dashboard
3. Add to `.env`:
   ```
   OPENROUTER_API_KEY=sk-or-v1-your-key-here
   ```

## 👥 Default Credentials

### Admin Account
- **User ID**: admin
- **Password**: admin123

### Farmer Account
- **User ID**: farmer1
- **Password**: farmer123

⚠️ **Change these in production!** Edit `users.json` and `app.py` line 16.

## 📁 Project Structure

```
vet-ai-app/
├── app.py                    # Flask application & API routes
├── requirements.txt          # Python dependencies
├── Dockerfile               # Container configuration
├── docker-compose.yml       # Multi-container orchestration
├── .env.example            # Environment variables template
├── static/
│   ├── uploads/            # Persistent uploaded files
│   └── temp_uploads/       # Temporary file processing
├── templates/
│   ├── login.html          # Authentication page
│   ├── admin_dashboard.html # Admin management panel
│   └── user_dashboard.html  # User interface
├── dataset/                # Reference animal images
├── animals.json            # Animal health records database
└── users.json              # User accounts
```

## 🔄 API Endpoints

### Authentication
- `POST /login` - User login
- `GET /logout` - User logout

### Admin Routes
- `GET /admin` - Admin dashboard
- `POST /admin/scan` - Scan & diagnose animal image
- `POST /admin/add_animal` - Add new animal record
- `POST /admin/edit_animal` - Update animal data
- `POST /admin/delete_animal` - Remove animal record
- `GET /admin/get_animal/<tag_id>` - Fetch animal details

### User Routes
- `GET /user` - User dashboard
- `POST /user/scan` - Analyze uploaded image (temporary)

### Shared Routes
- `POST /chat` - AI chat endpoint

## 🎯 Usage

### As Admin
1. Login with admin credentials
2. Upload animal images and register them
3. Add health records, vaccination history, weight
4. Monitor animal status with AI-generated reports

### As Farmer/User
1. Login with farmer credentials
2. Upload pet/animal images
3. Get instant health analysis
4. Chat with AI for specific concerns

## 📊 How Image Matching Works

1. **Feature Extraction**: Analyzes color histograms and edge detection
2. **Chi-Squared Distance**: Compares uploaded image to dataset
3. **Best Match**: Returns most similar animal from database
4. **Health Lookup**: Retrieves full health record for matched animal

## 🤖 AI Diagnosis Process

1. **Data Collection**: System gathers animal profile
2. **Symptom Analysis**: AI interprets health issues
3. **Diagnosis**: Generates possible conditions
4. **Risk Assessment**: Rates severity (Low/Medium/High)
5. **Recommendations**: Suggests care actions

## 🚀 Deployment

See [DEPLOYMENT_GUIDE.md](./DEPLOYMENT_GUIDE.md) for detailed instructions.

**Quick deploy to Render:**
```bash
git push origin main  # Render auto-deploys on push
```

## 🔒 Security Notes

- Change `SECRET_KEY` in production
- Use HTTPS only (auto on Render/Railway/Heroku)
- Store API keys in environment variables
- Regularly backup `animals.json` and `users.json`
- Never commit `.env` files

## 🐛 Troubleshooting

### Image Upload Fails
- Check image format (PNG, JPG, JPEG, BMP, WEBP)
- Max file size: 16MB
- Ensure dataset folder has reference images

### AI Responses Slow
- OpenRouter API takes 5-15 seconds
- Check internet connection
- Verify API key is valid

### No Animal Match Found
- Ensure dataset images are in `/dataset` folder
- Upload images must match animal type in dataset
- Try different image angles/lighting

## 📈 Performance Tips

- Cache animal features after first load
- Compress images before upload
- Use CDN for static files
- Scale Gunicorn workers: `--workers 8`

## 📝 License

Proprietary - Vet AI Application

## 💬 Support

For issues or questions:
1. Check DEPLOYMENT_GUIDE.md
2. Review Flask/OpenCV documentation
3. Verify API key and environment setup
4. Check application logs

---

**Ready to deploy?** → See [DEPLOYMENT_GUIDE.md](./DEPLOYMENT_GUIDE.md)
