# TRUSTGUARD AI — Professional Edition 2.0

**Tagline:** Verify Before You Apply. Protect Your Career.

TRUSTGUARD AI is an educational Flask + machine-learning prototype that screens job and internship messages for suspicious text patterns. It combines a TF-IDF + Logistic Regression classifier with explainable text rules and provides English/Tamil safety guidance.

## What's upgraded in version 2.0

- Hybrid risk indicator combining model probability and transparent rule signals.
- Eight explainable warning categories, including suspicious links and unknown software installation requests.
- Improved input validation and a friendly file-size error page.
- Dashboard summary with most frequent warning signals.
- Export complete local analysis history to UTF-8 CSV.
- `/health` endpoint reports model/database readiness and app version.
- Training script validates dataset columns/classes and saves held-out evaluation metrics as `models/evaluation_metrics.json`.
- Automated unit tests for core analysis rules and web routes.

## Technology stack

- Python 3.10+
- Flask
- scikit-learn (TF-IDF + Logistic Regression)
- pandas and joblib
- SQLite
- HTML, CSS and JavaScript

## Setup on Windows PowerShell

Open PowerShell in the `TRUSTGUARD_AI_Professional` folder:

```powershell
py -3.12 -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python train_model.py
python app.py
```

If PowerShell blocks activation, run:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\venv\Scripts\Activate.ps1
```

Open **http://127.0.0.1:5000** in your browser.

## Run tests

After installing requirements:

```powershell
python -m unittest discover -s tests -v
```

## Main pages and endpoints

| Route | Purpose |
|---|---|
| `/` | Home page and message scanner |
| `/analyze` | Analyse a submitted job message |
| `/dashboard` | Summary, warning insights and recent history |
| `/export.csv` | Download local analysis history as CSV |
| `/health` | JSON application/model/database health status |

## Project structure

```text
TRUSTGUARD_AI_Professional/
├── app.py
├── train_model.py
├── requirements.txt
├── README.md
├── dataset/
│   ├── job_posts.csv
│   └── DATASET_NOTE.txt
├── models/                 # generated model and evaluation report
├── database/               # local SQLite history
├── tests/
│   └── test_app.py
├── templates/
│   ├── base.html
│   ├── index.html
│   ├── result.html
│   └── dashboard.html
└── static/
    ├── css/style.css
    └── js/main.js
```

## Important limitations (read before presentation)

- The included dataset contains synthetic teaching/demo examples. Evaluation metrics are only a small held-out test on that dataset and are **not** evidence of real-world performance.
- A low risk indicator does not prove a job, recruiter or company is genuine. A high score is not a legal or definitive fraud verdict.
- The prototype analyses only the text pasted by the user. It does not verify company registration, recruiter identity, email ownership, website safety or live job listings against official services.
- Risk scores are heuristic indicators designed to support careful review, not calibrated probabilities of fraud.
- Do not paste OTPs, passwords, UPI PINs, bank details or other sensitive personal information.
- Analysis history is stored locally in `database/trustguard.db`. CSV export contains the original messages, so keep the downloaded file private.

## Suggested college demonstration flow

1. Start the app and open the scanner.
2. Try the genuine-style sample and review the result explanation.
3. Try the suspicious sample and compare warning signals and risk score.
4. Open the dashboard to show counts and frequent warning indicators.
5. Export the history as CSV.
6. Run the unit tests and show `models/evaluation_metrics.json` to explain model evaluation honestly.
