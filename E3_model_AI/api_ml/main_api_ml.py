from .models_api_ml import (
    Product, ProductWithPrediction,
    ImageRequest, ImagePrediction,
    Token
)
from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from datetime import timedelta
from pathlib import Path
from dotenv import load_dotenv
from .auth import get_current_user, create_access_token, authenticate_user
from ultralytics import YOLO
import joblib
import os
import requests
from PIL import Image
from io import BytesIO
from fastapi.responses import HTMLResponse, Response
from prometheus_client import Gauge, generate_latest
from evidently import Report
from evidently.presets import DataDriftPreset
import pandas as pd

# Charger le fichier .env
env_path = Path(__file__).parent / ".env"
load_dotenv(env_path)

# Détection de l'environnement
IS_DOCKER = os.path.exists("/app")
IS_CI = os.getenv("GITHUB_ACTIONS") == "true"

# Définir le chemin racine
if IS_DOCKER:
    BASE_DIR = Path("/app")
elif IS_CI:
    BASE_DIR = Path("E3_model_AI")
else:
    BASE_DIR = Path("/home/utilisateur/Documents/Certification/certification_global/E3_model_AI")

# Charger les modèles
MODEL_XGB_PATH = BASE_DIR / "model_ml" / "xgboost_weapon_classifier.pkl"
VECTORIZER_PATH = BASE_DIR / "model_ml" / "tfidf_vectorizer.pkl"
MODEL_YOLO_PATH = BASE_DIR / "model_ml" / "best.pt"

if not MODEL_XGB_PATH.exists() or not VECTORIZER_PATH.exists():
    raise FileNotFoundError("Le modèle XGBoost ou le vectorizer est introuvable.")
if not MODEL_YOLO_PATH.exists():
    raise FileNotFoundError("Le modèle YOLO 'best.pt' est introuvable.")

# Charger les modèles
model_xgb = joblib.load(MODEL_XGB_PATH)
vectorizer = joblib.load(VECTORIZER_PATH)
model_yolo = YOLO(str(MODEL_YOLO_PATH))
CONFIDENCE_THRESHOLD = 0.6

# Initialisation de FastAPI
app = FastAPI(
    title="API - Détection d'Armes",
    description="API combinant XGBoost (texte) et YOLO (image) pour détecter les armes sur des produits.",
    version="2.0.0"
)

# ==============================
# AUTHENTIFICATION
# ==============================
@app.post("/token", response_model=Token)
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=401, detail="Identifiants incorrects")
    access_token = create_access_token(data={"sub": user["username"]}, expires_delta=timedelta(minutes=60))
    return {"access_token": access_token, "token_type": "bearer"}

# ==============================
# PREDICTION TEXTE (XGBoost)
# ==============================
@app.post("/predict/", response_model=ProductWithPrediction)
def predict(data: Product, user: dict = Depends(get_current_user)):
    text = data.description + " " + data.title
    text_vect = vectorizer.transform([text])
    prediction = model_xgb.predict(text_vect)[0]
    return ProductWithPrediction(
        product_id=data.product_id,
        url=data.url,
        title=data.title,
        description=data.description,
        is_weapon_pred=int(prediction)
    )

# ==============================
# PREDICTION IMAGE (YOLO)
# ==============================
@app.post("/predict_image/", response_model=ImagePrediction)
def predict_image(data: ImageRequest, user: dict = Depends(get_current_user)):
    try:
        response = requests.get(data.image_url, timeout=5)
        if response.status_code != 200:
            raise HTTPException(status_code=400, detail="Image inaccessible")

        img = Image.open(BytesIO(response.content)).convert("RGB")
        results = model_yolo.predict(img)

        confidences = [
            box.conf.item()
            for r in results
            for box in r.boxes
            if box.conf.item() >= CONFIDENCE_THRESHOLD
        ]
        max_conf = max(confidences) if confidences else 0.0
        is_weapon = int(max_conf >= CONFIDENCE_THRESHOLD)

        return ImagePrediction(
            image_url=data.image_url,
            is_weapon_cv=is_weapon,
            confidence=max_conf
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors du traitement de l'image : {str(e)}")

# === GAUGES POUR PROMETHEUS ===
xgboost_drift_score = Gauge("xgboost_data_drift", "Score de dérive XGBoost")
yolo_drift_score = Gauge("yolo_data_drift", "Score de dérive YOLO")

@app.get("/metrics")
def prometheus_metrics():
    return Response(generate_latest(), media_type="text/plain")

@app.get("/monitor/refresh-drift")
def refresh_drift():
    try:
        ref_xgb = BASE_DIR / "monitoring/evidently/xgboost_reference_sample.csv"
        prod_xgb = BASE_DIR / "monitoring/evidently/xgboost_production_sample.csv"

        if ref_xgb.exists() and prod_xgb.exists():
            ref = pd.read_csv(ref_xgb)
            prod = pd.read_csv(prod_xgb)
            if "is_weapon" in ref.columns and "is_weapon_pred" not in ref.columns:
                ref = ref.rename(columns={"is_weapon": "is_weapon_pred"})
            ref.dropna(subset=["is_weapon_pred"], inplace=True)
            prod.dropna(subset=["is_weapon_pred"], inplace=True)
            ref["is_weapon_pred"] = ref["is_weapon_pred"].astype(int)
            prod["is_weapon_pred"] = prod["is_weapon_pred"].astype(int)
            report = Report(metrics=[DataDriftPreset()])
            report.run(reference_data=ref, current_data=prod)
            result = report.as_dict()
            score = result["metrics"][0]["result"]["dataset_drift"]
            xgboost_drift_score.set(score)

        ref_yolo = BASE_DIR / "monitoring/evidently/yolo_reference_sample.csv"
        prod_yolo = BASE_DIR / "monitoring/evidently/yolo_production_sample.csv"

        if ref_yolo.exists() and prod_yolo.exists():
            ref = pd.read_csv(ref_yolo)
            prod = pd.read_csv(prod_yolo)
            report = Report(metrics=[DataDriftPreset()])
            report.run(reference_data=ref, current_data=prod)
            result = report.as_dict()
            score = result["metrics"][0]["result"]["dataset_drift"]
            yolo_drift_score.set(score)

        return {"status": "OK", "message": "Scores de dérive mis à jour"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur de monitoring Evidently : {str(e)}")

@app.get("/monitor/xgboost", response_class=HTMLResponse)
def xgboost_report():
    ref = BASE_DIR / "monitoring/evidently/xgboost_reference_sample.csv"
    prod = BASE_DIR / "monitoring/evidently/xgboost_production_sample.csv"

    if not ref.exists() or not prod.exists():
        raise HTTPException(status_code=404, detail="Fichiers de monitoring manquants")

    df_ref = pd.read_csv(ref)
    df_prod = pd.read_csv(prod)

    if "is_weapon" in df_ref.columns and "is_weapon_pred" not in df_ref.columns:
        df_ref = df_ref.rename(columns={"is_weapon": "is_weapon_pred"})

    df_ref = df_ref.dropna(subset=["is_weapon_pred"])
    df_prod = df_prod.dropna(subset=["is_weapon_pred"])
    df_ref["is_weapon_pred"] = df_ref["is_weapon_pred"].astype(int)
    df_prod["is_weapon_pred"] = df_prod["is_weapon_pred"].astype(int)

    report = Report(metrics=[DataDriftPreset()])
    xgb_report = report.run(reference_data=df_ref, current_data=df_prod)
    report_path = BASE_DIR / "monitoring/evidently/xgboost_drift_report.html"
    xgb_report
    xgb_report.save_html("report_path")
    return HTMLResponse(content=report_path.read_text(), status_code=200)
        

@app.get("/monitor/yolo", response_class=HTMLResponse)
def yolo_report():
    ref = BASE_DIR / "monitoring/evidently/yolo_reference_sample.csv"
    prod = BASE_DIR / "monitoring/evidently/yolo_production_sample.csv"

    if not ref.exists() or not prod.exists():
        raise HTTPException(status_code=404, detail="Fichiers de monitoring YOLO manquants")

    df_ref = pd.read_csv(ref)
    df_prod = pd.read_csv(prod)

    report = Report(metrics=[DataDriftPreset()])
    report.run(reference_data=df_ref, current_data=df_prod)
    report_path = BASE_DIR / "monitoring/evidently/yolo_drift_report.html"
    report.save_html(str(report_path))
    return HTMLResponse(content=report_path.read_text(), status_code=200)
