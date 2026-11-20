from pathlib import Path
import json
import pandas as pd
import joblib
import sklearn
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix, classification_report

BASE = Path(__file__).resolve().parent
DATA = BASE / "dataset" / "job_posts.csv"
MODEL_DIR = BASE / "models"
MODEL_DIR.mkdir(exist_ok=True)


def main():
    if not DATA.exists():
        raise FileNotFoundError(f"Dataset not found: {DATA}")
    df = pd.read_csv(DATA)
    required = {"text", "label"}
    if not required.issubset(df.columns):
        raise ValueError("Dataset must contain 'text' and 'label' columns.")
    df = df.dropna(subset=["text", "label"]).copy()
    df["text"] = df["text"].astype(str).str.strip()
    df = df[df["text"].str.len() >= 10].drop_duplicates(subset=["text"])
    df["label"] = pd.to_numeric(df["label"], errors="raise").astype(int)
    if set(df["label"].unique()) != {0, 1}:
        raise ValueError("Dataset labels must be 0=legitimate and 1=potentially fraudulent.")
    counts = df["label"].value_counts()
    if counts.min() < 5:
        raise ValueError("At least five unique examples per class are required.")

    X_train, X_test, y_train, y_test = train_test_split(
        df["text"], df["label"], test_size=0.25, random_state=42, stratify=df["label"]
    )
    vectorizer = TfidfVectorizer(ngram_range=(1, 2), max_features=30000, strip_accents="unicode",
                                 lowercase=True, sublinear_tf=True, min_df=1)
    X_train_vec = vectorizer.fit_transform(X_train)
    X_test_vec = vectorizer.transform(X_test)
    model = LogisticRegression(max_iter=2000, class_weight="balanced", C=1.5, random_state=42)
    model.fit(X_train_vec, y_train)
    predictions = model.predict(X_test_vec)

    metrics = {
        "dataset_rows": int(len(df)), "train_rows": int(len(X_train)), "test_rows": int(len(X_test)),
        "class_counts": {"legitimate_0": int(counts.get(0, 0)), "suspicious_1": int(counts.get(1, 0))},
        "accuracy_percent": round(accuracy_score(y_test, predictions) * 100, 2),
        "precision_percent": round(precision_score(y_test, predictions, zero_division=0) * 100, 2),
        "recall_percent": round(recall_score(y_test, predictions, zero_division=0) * 100, 2),
        "f1_percent": round(f1_score(y_test, predictions, zero_division=0) * 100, 2),
        "confusion_matrix_tn_fp_fn_tp": confusion_matrix(y_test, predictions, labels=[0, 1]).tolist(),
        "classification_report": classification_report(y_test, predictions, labels=[0, 1],
            target_names=["Legitimate", "Potentially suspicious"], output_dict=True, zero_division=0),
        "model": "TF-IDF (1-2 grams) + Logistic Regression",
        "scikit_learn_version": sklearn.__version__,
        "dataset_notice": "Included dataset is synthetic teaching/demo data; metrics are not real-world performance claims."
    }
    joblib.dump(model, MODEL_DIR / "scam_model.joblib")
    joblib.dump(vectorizer, MODEL_DIR / "tfidf_vectorizer.joblib")
    (MODEL_DIR / "evaluation_metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")

    print("\n=== HELD-OUT TEST EVALUATION ===")
    print(f"Dataset rows : {metrics['dataset_rows']}")
    print(f"Train / test : {metrics['train_rows']} / {metrics['test_rows']}")
    print(f"Accuracy     : {metrics['accuracy_percent']:.2f}%")
    print(f"Precision    : {metrics['precision_percent']:.2f}%")
    print(f"Recall       : {metrics['recall_percent']:.2f}%")
    print(f"F1-score     : {metrics['f1_percent']:.2f}%")
    print("Confusion matrix [ [TN, FP], [FN, TP] ]:")
    print(metrics["confusion_matrix_tn_fp_fn_tp"])
    print("\nModel files and evaluation_metrics.json saved in models/.")
    print("NOTE: Synthetic demo data; these metrics do not represent real-world accuracy.")


if __name__ == "__main__":
    main()
