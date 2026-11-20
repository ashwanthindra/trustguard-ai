from flask import Flask, render_template, request, jsonify, Response
from pathlib import Path
from datetime import datetime
import csv
import io
import sqlite3
import joblib
import re

BASE = Path(__file__).resolve().parent
MODEL_DIR = BASE / "models"
DB_PATH = BASE / "database" / "trustguard.db"

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 1 * 1024 * 1024

WARNING_GUIDE = {
    "Upfront payment request": ("An employer asking you to pay before selection is a warning sign.", "வேலை உறுதி செய்வதற்கு முன் பணம் கேட்பது எச்சரிக்கை அறிகுறி."),
    "Unrealistic income promise": ("Very high income claims without clear requirements may be misleading.", "தகுதி அல்லது வேலை விவரம் இல்லாமல் அதிக வருமானம் உறுதி செய்வது சந்தேகத்திற்குரியது."),
    "Urgency or pressure": ("Pressure to act immediately can stop you from checking the offer carefully.", "உடனே முடிவு செய்ய அழுத்தம் கொடுத்தால், சரிபார்க்க நேரம் எடுத்துக்கொள்ளுங்கள்."),
    "Sensitive information request": ("Never share OTPs, passwords, UPI PINs or banking credentials with recruiters.", "OTP, password, UPI PIN அல்லது வங்கி ரகசியங்களை recruiter-க்கு பகிர வேண்டாம்."),
    "Unprofessional recruitment language": ("A genuine hiring process normally explains the role and selection steps.", "உண்மையான வேலைவாய்ப்பு பொதுவாக பணியின் விவரம் மற்றும் தேர்வு முறையை விளக்கும்."),
    "Unverified communication channel": ("A personal email or messaging-only contact should be independently verified.", "தனிப்பட்ட email அல்லது chat மட்டும் இருந்தால் நிறுவனத்தின் அதிகாரப்பூர்வ வழியில் சரிபார்க்கவும்."),
    "Suspicious link or domain": ("Unexpected shortened links or look-alike domains should be checked carefully before opening.", "தெரியாத குறுக்கப்பட்ட link அல்லது போலியான domain-ஐ திறப்பதற்கு முன் கவனமாக சரிபார்க்கவும்."),
    "Request to install unknown software": ("Do not install unknown apps or remote-access tools at a recruiter's request.", "Recruiter கேட்டதால் தெரியாத app அல்லது remote-access software-ஐ install செய்ய வேண்டாம்.")
}

RULES = [
    ("Upfront payment request", [r"registration fee", r"pay\s*₹?\s*\d+", r"processing fee", r"security deposit", r"training fee", r"payment required", r"send money", r"pay first", r"refundable fee"]),
    ("Unrealistic income promise", [r"earn\s*₹?\s*\d{2,}", r"guaranteed income", r"easy money", r"high salary.*no experience", r"daily income", r"salary up to\s*₹?\s*\d+"]),
    ("Urgency or pressure", [r"immediately", r"limited slots", r"within 24 hours", r"urgent", r"act now", r"today only", r"last chance"]),
    ("Sensitive information request", [r"\botp\b", r"bank password", r"upi pin", r"card number", r"aadhaar.*send", r"pan.*send", r"account credentials"]),
    ("Unprofessional recruitment language", [r"no interview", r"selected.*without", r"100% guaranteed job", r"no skills required.*high", r"instant joining.*no interview"]),
    ("Unverified communication channel", [r"whatsapp only", r"telegram only", r"personal gmail", r"contact.*@gmail\.com", r"contact.*@yahoo\.com"]),
    ("Suspicious link or domain", [r"bit\.ly/", r"tinyurl\.com/", r"t\.co/", r"\.xyz\b", r"\.top\b", r"login[-_]verify"]),
    ("Request to install unknown software", [r"install.*(apk|anydesk|teamviewer|remote access)", r"download.*apk", r"screen sharing app"])
]


def get_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    return con


def init_db():
    with get_db() as con:
        con.execute("""CREATE TABLE IF NOT EXISTS analyses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            message TEXT NOT NULL,
            prediction TEXT NOT NULL,
            probability REAL NOT NULL,
            risk_score INTEGER NOT NULL,
            risk_level TEXT NOT NULL,
            indicators TEXT NOT NULL
        )""")
        columns = {row["name"] for row in con.execute("PRAGMA table_info(analyses)")}
        if "risk_level" not in columns:
            con.execute("ALTER TABLE analyses ADD COLUMN risk_level TEXT NOT NULL DEFAULT 'Low'")


def load_model():
    model_path = MODEL_DIR / "scam_model.joblib"
    vec_path = MODEL_DIR / "tfidf_vectorizer.joblib"
    if model_path.exists() and vec_path.exists():
        try:
            return joblib.load(model_path), joblib.load(vec_path)
        except (OSError, ValueError, EOFError):
            return None, None
    return None, None


def indicators_for(message):
    text = message.lower()
    return [label for label, patterns in RULES if any(re.search(pattern, text) for pattern in patterns)]


def analyse_message(message):
    model, vectorizer = load_model()
    if model is None or vectorizer is None:
        raise RuntimeError("AI model is not trained yet. Run: python train_model.py")

    features = vectorizer.transform([message])
    predicted = int(model.predict(features)[0])
    probabilities = model.predict_proba(features)[0]
    classes = list(model.classes_)
    scam_probability = float(probabilities[classes.index(1)]) if 1 in classes else float(predicted)
    indicators = indicators_for(message)

    # Hybrid score: model probability + transparent rule evidence. It is an indicator, not a fraud verdict.
    rule_score = min(100, len(indicators) * 18)
    score = round(min(100, max(0, scam_probability * 65 + rule_score * 0.35)))
    level = "High" if score >= 65 else "Medium" if score >= 35 else "Low"
    label = "Potentially suspicious patterns found" if predicted == 1 else "No strong scam pattern detected"
    advice_en = ("Pause. Do not pay or share personal information. Verify the employer using contact details found independently."
                 if level == "High" else "Check the official company careers page, recruiter identity and written job details before proceeding.")
    advice_ta = ("நிறுத்தி சரிபார்க்கவும். பணம் செலுத்தவோ தனிப்பட்ட தகவல்களை பகிரவோ வேண்டாம். நிறுவனத்தின் அதிகாரப்பூர்வ வழியில் உறுதி செய்யுங்கள்."
                 if level == "High" else "நிறுவனத்தின் அதிகாரப்பூர்வ careers page, recruiter அடையாளம் மற்றும் வேலை விவரங்களை சரிபார்த்த பிறகே தொடருங்கள்.")
    return {
        "prediction": label, "probability": round(scam_probability * 100, 1),
        "risk_score": score, "risk_level": level, "indicators": indicators,
        "warning_details": [WARNING_GUIDE[item] for item in indicators],
        "advice_en": advice_en, "advice_ta": advice_ta,
        "model_probability": round(scam_probability * 100, 1),
        "rule_signal_count": len(indicators)
    }


@app.errorhandler(413)
def too_large(_error):
    return render_template("index.html", error="Message is too large. Please keep it under 10,000 characters."), 413


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/analyze", methods=["POST"])
def analyze():
    message = (request.form.get("message") or "").strip()
    if len(message) < 20:
        return render_template("index.html", error="Please enter at least 20 characters.", message=message), 400
    if len(message) > 10000:
        return render_template("index.html", error="Maximum 10,000 characters allowed.", message=message), 400
    try:
        result = analyse_message(message)
        with get_db() as con:
            con.execute("""INSERT INTO analyses
                (created_at,message,prediction,probability,risk_score,risk_level,indicators)
                VALUES (?,?,?,?,?,?,?)""",
                (datetime.now().strftime("%d %b %Y, %I:%M %p"), message,
                 result["prediction"], result["probability"], result["risk_score"],
                 result["risk_level"], ", ".join(result["indicators"])))
        return render_template("result.html", result=result, message=message)
    except RuntimeError as exc:
        return render_template("index.html", error=str(exc), message=message), 503


@app.route("/dashboard")
def dashboard():
    with get_db() as con:
        rows = con.execute("SELECT * FROM analyses ORDER BY id DESC LIMIT 100").fetchall()
        total = con.execute("SELECT COUNT(*) FROM analyses").fetchone()[0]
        high = con.execute("SELECT COUNT(*) FROM analyses WHERE risk_level='High'").fetchone()[0]
        medium = con.execute("SELECT COUNT(*) FROM analyses WHERE risk_level='Medium'").fetchone()[0]
        low = total - high - medium
        all_indicators = con.execute("SELECT indicators FROM analyses WHERE indicators <> ''").fetchall()
    signal_counts = {}
    for item in all_indicators:
        for signal in item["indicators"].split(","):
            signal = signal.strip()
            if signal:
                signal_counts[signal] = signal_counts.get(signal, 0) + 1
    top_signals = sorted(signal_counts.items(), key=lambda pair: pair[1], reverse=True)[:5]
    return render_template("dashboard.html", rows=rows, total=total, high=high, medium=medium, low=low, top_signals=top_signals)


@app.route("/export.csv")
def export_csv():
    with get_db() as con:
        rows = con.execute("SELECT created_at,message,prediction,probability,risk_score,risk_level,indicators FROM analyses ORDER BY id DESC").fetchall()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Date and time", "Message", "Model result", "Suspicious probability (%)", "Risk indicator score", "Risk level", "Warning signals"])
    writer.writerows([tuple(row) for row in rows])
    return Response("\ufeff" + output.getvalue(), mimetype="text/csv; charset=utf-8", headers={"Content-Disposition": "attachment; filename=trustguard_analysis_history.csv"})


@app.route("/health")
def health():
    model, vectorizer = load_model()
    return jsonify({"status": "ok", "model_loaded": model is not None and vectorizer is not None,
                    "database_ready": DB_PATH.exists(), "version": "2.0.0"})


init_db()

if __name__ == "__main__":
    app.run(debug=False)
