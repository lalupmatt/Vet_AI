from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash
import os
import json
import cv2
import numpy as np
import requests
import time
from functools import wraps
from werkzeug.security import check_password_hash
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = "vetai_secret_key_change_in_production"

# ─── Paths ─────────────────────────────────────────────────────────────
BASE_DIR           = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER      = os.path.join(BASE_DIR, "static/uploads")
TEMP_UPLOAD_FOLDER = os.path.join(BASE_DIR, "static/temp_uploads")
DATASET_PATH       = os.path.join(BASE_DIR, "dataset")
USERS_FILE         = os.path.join(BASE_DIR, "users.json")
ANIMALS_FILE       = os.path.join(BASE_DIR, "animals.json")

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(TEMP_UPLOAD_FOLDER, exist_ok=True)
os.makedirs(DATASET_PATH, exist_ok=True)

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "bmp", "webp"}

# ─── API Config (OpenRouter) ────────────────────────────────────────────
API_KEY = os.getenv("OPENROUTER_API_KEY")
API_URL = "https://openrouter.ai/api/v1/chat/completions"

CURRENT_ANIMAL = None


# ════════════════════════════════════════════════════════════════════════
#  JSON HELPERS  (safe read / write)
# ════════════════════════════════════════════════════════════════════════

def load_json(filepath, default=None):
    """Read a JSON file and return its contents, or `default` if missing."""
    if default is None:
        default = []
    if not os.path.exists(filepath):
        return default
    try:
        with open(filepath, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return default


def save_json(filepath, data):
    """Write data to a JSON file atomically."""
    tmp = filepath + ".tmp"
    with open(tmp, "w") as f:
        json.dump(data, f, indent=2)
    os.replace(tmp, filepath)


# ════════════════════════════════════════════════════════════════════════
#  AUTH HELPERS
# ════════════════════════════════════════════════════════════════════════

def get_user(user_id):
    users = load_json(USERS_FILE, [])
    for u in users:
        if u.get("id") == user_id:
            return u
    return None


def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated


def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login"))
        if session.get("role") != "admin":
            flash("Admin access required.", "error")
            return redirect(url_for("user_dashboard"))
        return f(*args, **kwargs)
    return decorated


# ════════════════════════════════════════════════════════════════════════
#  ANIMALS JSON HELPERS
# ════════════════════════════════════════════════════════════════════════

def get_all_animals():
    return load_json(ANIMALS_FILE, [])


def get_animal_by_image(image_filename):
    for a in get_all_animals():
        if a.get("image") == image_filename:
            return a
    return None


def get_animal_by_tag(tag_id):
    for a in get_all_animals():
        if a.get("tag_id") == tag_id:
            return a
    return None


def upsert_animal(animal_data):
    """Insert or update an animal record (matched by tag_id)."""
    animals = get_all_animals()
    for i, a in enumerate(animals):
        if a.get("tag_id") == animal_data.get("tag_id"):
            animals[i] = animal_data
            save_json(ANIMALS_FILE, animals)
            return
    animals.append(animal_data)
    save_json(ANIMALS_FILE, animals)


def delete_animal_by_tag(tag_id):
    animals = [a for a in get_all_animals() if a.get("tag_id") != tag_id]
    save_json(ANIMALS_FILE, animals)


def fallback_animal_lookup(match_filename):
    """Check animals.json first, then fall back to legacy database.json."""
    animal = get_animal_by_image(match_filename)
    if animal:
        return animal
    if os.path.exists("database.json"):
        try:
            with open("database.json") as f:
                db = json.load(f)
            return db.get(match_filename)
        except Exception:
            pass
    return None


# ════════════════════════════════════════════════════════════════════════
#  IMAGE MATCHING
# ════════════════════════════════════════════════════════════════════════

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def extract_features(image_path):
    img = cv2.imread(image_path)
    if img is None:
        return None
    img = cv2.resize(img, (128, 128))
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    hist_h = cv2.calcHist([hsv], [0], None, [32], [0, 180]).flatten()
    hist_s = cv2.calcHist([hsv], [1], None, [32], [0, 256]).flatten()
    hist_v = cv2.calcHist([hsv], [2], None, [32], [0, 256]).flatten()
    color_hist = np.concatenate([hist_h, hist_s, hist_v])
    color_hist /= (color_hist.sum() + 1e-6)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(gray, 50, 150)
    edge_hist = cv2.calcHist([edges], [0], None, [16], [0, 256]).flatten()
    edge_hist /= (edge_hist.sum() + 1e-6)
    patch = cv2.resize(gray, (16, 16)).flatten().astype(np.float32) / 255.0
    return np.concatenate([color_hist, edge_hist, patch])


def chi_squared_distance(h1, h2):
    eps = 1e-10
    return 0.5 * np.sum(((h1 - h2) ** 2) / (h1 + h2 + eps))


def find_best_match(uploaded_path):
    uploaded_feat = extract_features(uploaded_path)
    if uploaded_feat is None:
        return None
    scores = {}
    for filename in os.listdir(DATASET_PATH):
        if not allowed_file(filename):
            continue
        feat = extract_features(os.path.join(DATASET_PATH, filename))
        if feat is not None:
            scores[filename] = chi_squared_distance(uploaded_feat, feat)
    return min(scores, key=scores.get) if scores else None


# ════════════════════════════════════════════════════════════════════════
#  AI FUNCTIONS  (unchanged from original)
# ════════════════════════════════════════════════════════════════════════

def call_ai(prompt):
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "http://localhost:5000",
        "X-Title": "Vet AI"
    }
    payload = {
        "model": "meta-llama/llama-3-8b-instruct",
        "messages": [
            {"role": "system", "content": "You are a veterinary AI assistant."},
            {"role": "user", "content": prompt}
        ]
    }
    try:
        resp = requests.post(API_URL, headers=headers, json=payload, timeout=15)
        print("STATUS:", resp.status_code)
        if resp.status_code == 200:
            return resp.json()["choices"][0]["message"]["content"]
        return f"AI Error: {resp.text}"
    except Exception as e:
        return f"Error: {str(e)}"


def ai_health_diagnosis(animal_data):
    prompt = f"""
You are a professional veterinary doctor.
Analyze the animal condition deeply and give a clinical diagnosis.

Include:
- Possible diseases
- Symptoms explanation
- Risk level (Low / Medium / High)

Animal Data:
Species: {animal_data.get("species")}
Age: {animal_data.get("age")}
Vaccination: {animal_data.get("vaccination")}
Health Issues: {animal_data.get("health")}
Medical History: {animal_data.get("medical_history")}

Give clear bullet points.
"""
    return call_ai(prompt)


def ai_generate_health_report(animal_data, diagnosis):
    prompt = f"""
You are a veterinary assistant AI.
Create a simple health report for farmers. Keep it SHORT and EASY.

Include:
- Overall condition (1 line)
- Health score out of 100
- 2-3 simple care tips

Animal Data:
Species: {animal_data.get("species")}
Age: {animal_data.get("age")}
Vaccination: {animal_data.get("vaccination")}
Health: {animal_data.get("health")}

Do NOT be technical.
"""
    summary = call_ai(prompt)
    score = 85
    if "risk" in diagnosis.lower():
        score = 60
    if "high" in diagnosis.lower():
        score = 40
    return {
        "summary": summary,
        "health_score": score,
        "status_badge": "Healthy" if score > 70 else "Needs Attention",
        "next_checkup": animal_data.get("next_checkup", "Not scheduled"),
        "action_items": [
            "Provide clean water",
            "Maintain balanced diet",
            "Schedule vet visit if needed"
        ]
    }


def ai_chat_reply(user_message):
    global CURRENT_ANIMAL
    context = ""
    if CURRENT_ANIMAL:
        context = f"""
Current Animal:
Name: {CURRENT_ANIMAL.get('name')}
Species: {CURRENT_ANIMAL.get('species')}
Age: {CURRENT_ANIMAL.get('age')}
Vaccination: {CURRENT_ANIMAL.get('vaccination')}
"""
    prompt = f"{context}\nUser Question: {user_message}\n\nAnswer like a veterinary assistant in simple terms."
    return call_ai(prompt)


# ════════════════════════════════════════════════════════════════════════
#  AUTH ROUTES
# ════════════════════════════════════════════════════════════════════════

@app.route("/login", methods=["GET", "POST"])
def login():
    if "user_id" in session:
        return redirect(url_for("admin_dashboard" if session.get("role") == "admin" else "user_dashboard"))

    error = None
    if request.method == "POST":
        uid  = request.form.get("user_id", "").strip()
        pwd  = request.form.get("password", "").strip()
        user = get_user(uid)

        if user and user.get("password") == pwd:
            session["user_id"] = user["id"]
            session["role"]    = user["role"]
            session["name"]    = user.get("name", user["id"])
            dest = "admin_dashboard" if user["role"] == "admin" else "user_dashboard"
            return redirect(url_for(dest))
        else:
            error = "Invalid ID or password. Please try again."

    return render_template("login.html", error=error)


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/")
def index():
    if "user_id" not in session:
        return redirect(url_for("login"))
    return redirect(url_for("admin_dashboard" if session.get("role") == "admin" else "user_dashboard"))


# ════════════════════════════════════════════════════════════════════════
#  ADMIN ROUTES
# ════════════════════════════════════════════════════════════════════════

@app.route("/admin")
@admin_required
def admin_dashboard():
    animals = get_all_animals()
    return render_template("admin_dashboard.html", animals=animals, user=session)


@app.route("/admin/scan", methods=["POST"])
@admin_required
def admin_scan():
    global CURRENT_ANIMAL
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"})
    file = request.files["file"]
    if not file.filename or not allowed_file(file.filename):
        return jsonify({"error": "Invalid file type"})

    filepath = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(filepath)

    match = find_best_match(filepath)
    if not match:
        return jsonify({"error": "No match found in dataset"})

    animal_data = fallback_animal_lookup(match)
    if not animal_data:
        return jsonify({"error": "Animal record not found"})

    CURRENT_ANIMAL = animal_data
    diagnosis = ai_health_diagnosis(animal_data)
    report    = ai_generate_health_report(animal_data, diagnosis)

    return jsonify({
        "success":        True,
        "match":          match,
        "animal":         animal_data,
        "diagnosis":      diagnosis,
        "report":         report,
        "uploaded_image": file.filename
    })


@app.route("/admin/add_animal", methods=["POST"])
@admin_required
def admin_add_animal():
    try:
        if "image" not in request.files:
            return jsonify({"status": "error", "message": "No image uploaded"})
        file = request.files["image"]
        if not file.filename or not allowed_file(file.filename):
            return jsonify({"status": "error", "message": "Invalid image"})

        filename = file.filename
        # Save to dataset (permanent)
        file.save(os.path.join(DATASET_PATH, filename))

        raw_history = request.form.get("medical_history", "")
        medical_history = [h.strip() for h in raw_history.split(",") if h.strip()]

        new_animal = {
            "tag_id":          request.form.get("tag_id"),
            "name":            request.form.get("name"),
            "species":         request.form.get("species"),
            "owner":           request.form.get("owner"),
            "age":             request.form.get("age"),
            "weight":          request.form.get("weight"),
            "location":        request.form.get("location"),
            "vaccination":     request.form.get("vaccination"),
            "health":          request.form.get("health"),
            "next_checkup":    request.form.get("next_checkup"),
            "medical_history": medical_history,
            "notes":           request.form.get("notes", ""),
            "image":           filename
        }

        upsert_animal(new_animal)
        return jsonify({"status": "success", "message": "Animal added successfully!"})

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})


@app.route("/admin/edit_animal", methods=["POST"])
@admin_required
def admin_edit_animal():
    try:
        data   = request.get_json()
        tag_id = data.get("tag_id")
        animals = get_all_animals()

        for i, a in enumerate(animals):
            if a.get("tag_id") == tag_id:
                editable = ["name", "species", "owner", "age", "weight",
                            "location", "vaccination", "health", "next_checkup", "notes"]
                for field in editable:
                    if field in data:
                        animals[i][field] = data[field]

                if "medical_history" in data:
                    mh = data["medical_history"]
                    animals[i]["medical_history"] = (
                        mh if isinstance(mh, list)
                        else [h.strip() for h in mh.split(",") if h.strip()]
                    )

                save_json(ANIMALS_FILE, animals)
                return jsonify({"status": "success", "message": "Animal updated!"})

        return jsonify({"status": "error", "message": "Animal not found"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})


@app.route("/admin/delete_animal", methods=["POST"])
@admin_required
def admin_delete_animal():
    try:
        data = request.get_json()
        delete_animal_by_tag(data.get("tag_id"))
        return jsonify({"status": "success", "message": "Animal deleted."})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})


@app.route("/admin/get_animal/<tag_id>")
@admin_required
def admin_get_animal(tag_id):
    animal = get_animal_by_tag(tag_id)
    if animal:
        return jsonify(animal)
    return jsonify({"error": "Not found"}), 404


# ════════════════════════════════════════════════════════════════════════
#  USER ROUTES
# ════════════════════════════════════════════════════════════════════════

@app.route("/user")
@login_required
def user_dashboard():
    return render_template("user_dashboard.html", user=session)


@app.route("/user/scan", methods=["POST"])
@login_required
def user_scan():
    global CURRENT_ANIMAL
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"})
    file = request.files["file"]
    if not file.filename or not allowed_file(file.filename):
        return jsonify({"error": "Invalid file type"})

    # Temp save — not stored in dataset, not written to JSON
    temp_path = os.path.join(TEMP_UPLOAD_FOLDER, file.filename)
    file.save(temp_path)

    match = find_best_match(temp_path)

    # Clean up temp file immediately
    try:
        os.remove(temp_path)
    except OSError:
        pass

    if not match:
        return jsonify({"error": "No match found in dataset"})

    animal_data = fallback_animal_lookup(match)
    if not animal_data:
        return jsonify({"error": "Animal record not found"})

    CURRENT_ANIMAL = animal_data
    diagnosis = ai_health_diagnosis(animal_data)
    report    = ai_generate_health_report(animal_data, diagnosis)

    return jsonify({
        "success":   True,
        "match":     match,
        "animal":    animal_data,
        "diagnosis": diagnosis,
        "report":    report
        # NOTE: No uploaded_image key — file is not stored permanently
    })


# ════════════════════════════════════════════════════════════════════════
#  SHARED ROUTES
# ════════════════════════════════════════════════════════════════════════

@app.route("/chat", methods=["POST"])
@login_required
def chat():
    data    = request.get_json()
    message = data.get("message", "")
    reply   = ai_chat_reply(message)
    return jsonify({"reply": reply})


# Legacy endpoint — now requires admin
@app.route("/add_animal", methods=["POST"])
@admin_required
def add_animal_legacy():
    return admin_add_animal()


# ─── Run ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app.run(debug=True)