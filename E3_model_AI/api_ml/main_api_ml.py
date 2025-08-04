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
from fastapi.responses import HTMLResponse, Response, RedirectResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from prometheus_client import Gauge, generate_latest
from prometheus_fastapi_instrumentator import Instrumentator
from evidently import Report, Dataset, DataDefinition
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

# Instrumentateur Prometheus
instrumentator = Instrumentator()
instrumentator.instrument(app).expose(app, include_in_schema=False, should_gzip=True)

# Monter les fichiers Evidently statiques
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "monitoring" / "evidently")), name="static")

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

from collections import defaultdict
import re

# === GAUGES POUR PROMETHEUS (dynamique)
gauges = defaultdict(dict)

def sanitize(name):
    return re.sub(r"[^a-zA-Z0-9_:]", "_", name).lower().strip("_")

def set_prometheus_metric(metric_name, value, labels=None, prefix=None):
    full_name = f"{prefix}_{metric_name}" if prefix else metric_name
    key = (full_name, tuple(sorted((labels or {}).items())))
    if key not in gauges[prefix or "default"]:
        if labels:
            gauges[prefix or "default"][key] = Gauge(full_name, f"Métrique Evidently : {full_name}", list(labels.keys()))
        else:
            gauges[prefix or "default"][key] = Gauge(full_name, f"Métrique Evidently : {full_name}")
    if labels:
        gauges[prefix or "default"][key].labels(**labels).set(value)
    else:
        gauges[prefix or "default"][key].set(value)

@app.get("/monitor/refresh-drift")
def refresh_drift():
    try:
        def process_drift(ref_path, prod_path, prefix: str):
            if not ref_path.exists() or not prod_path.exists():
                return

            ref = pd.read_csv(ref_path)
            prod = pd.read_csv(prod_path)

            if "is_weapon" in ref.columns and "is_weapon_pred" not in ref.columns:
                ref = ref.rename(columns={"is_weapon": "is_weapon_pred"})

            ref = ref.dropna(subset=["title", "description", "is_weapon_pred"])
            prod = prod.dropna(subset=["title", "description", "is_weapon_pred"])

            definition = DataDefinition(
                categorical_columns=["is_weapon_pred"],
                text_columns=["title", "description"]
            )

            ref_dataset = Dataset.from_pandas(ref, data_definition=definition)
            prod_dataset = Dataset.from_pandas(prod, data_definition=definition)

            report = Report(metrics=[DataDriftPreset()])
            my_eval = report.run(reference_data=ref_dataset, current_data=prod_dataset)
            result = my_eval.dict()

            for metric in result.get("metrics", []):
                metric_id = sanitize(metric.get("metric_id", "unknown_metric"))
                metric_value = metric.get("value", {})

                if isinstance(metric_value, (int, float)):
                    metric_name = sanitize(f"evidently_{metric_id}")
                    set_prometheus_metric(metric_name, metric_value, prefix=prefix)

                elif isinstance(metric_value, dict):
                    for key, value in metric_value.items():
                        if isinstance(value, (int, float)):
                            metric_name = sanitize(f"evidently_{metric_id}_{key}")
                            set_prometheus_metric(metric_name, value, prefix=prefix)

                # Si présence du détail par colonnes
                if metric_id == "datadrift" and "drift_by_columns" in metric_value:
                    for col, details in metric_value["drift_by_columns"].items():
                        col_key = sanitize(col)
                        drifted = 1 if details.get("drift_detected") else 0
                        p_val = details.get("p_value", 0)
                        set_prometheus_metric("column_drifted", drifted, labels={"column": col_key}, prefix=prefix)
                        set_prometheus_metric("column_p_value", p_val, labels={"column": col_key}, prefix=prefix)

        # XGBoost
        process_drift(
            ref_path=BASE_DIR / "monitoring/evidently/xgboost_reference_sample.csv",
            prod_path=BASE_DIR / "monitoring/evidently/xgboost_production_sample.csv",
            prefix="xgb"
        )

        # YOLO
        process_drift(
            ref_path=BASE_DIR / "monitoring/evidently/yolo_reference_sample.csv",
            prod_path=BASE_DIR / "monitoring/evidently/yolo_production_sample.csv",
            prefix="yolo"
        )

        return {"status": "OK", "message": "Toutes les métriques Evidently ont été mises à jour."}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur Evidently : {str(e)}")


@app.get("/monitor/xgboost")
def xgboost_report_link():
    return RedirectResponse(url="/static/xgboost_drift_report.html")

@app.get("/monitor/yolo")
def yolo_report_link():
    return RedirectResponse(url="/static/yolo_drift_report.html")

@app.get("/metrics")
def metrics():
    return PlainTextResponse(generate_latest(), media_type="text/plain")

# @app.get("/monitor/xgboost", response_class=HTMLResponse)
# def xgboost_report():
#     ref = BASE_DIR / "monitoring/evidently/xgboost_reference_sample.csv"
#     prod = BASE_DIR / "monitoring/evidently/xgboost_production_sample.csv"

#     if not ref.exists() or not prod.exists():
#         raise HTTPException(status_code=404, detail="Fichiers de monitoring manquants")

#     df_ref = pd.read_csv(ref)
#     df_prod = pd.read_csv(prod)

#     if "is_weapon" in df_ref.columns and "is_weapon_pred" not in df_ref.columns:
#         df_ref = df_ref.rename(columns={"is_weapon": "is_weapon_pred"})

#     df_ref = df_ref.dropna(subset=["is_weapon_pred"])
#     df_prod = df_prod.dropna(subset=["is_weapon_pred"])
#     df_ref["is_weapon_pred"] = df_ref["is_weapon_pred"].astype(int)
#     df_prod["is_weapon_pred"] = df_prod["is_weapon_pred"].astype(int)

#     report = Report(metrics=[DataDriftPreset()])
#     xgb_report = report.run(reference_data=df_ref, current_data=df_prod)
#     report_path = BASE_DIR / "monitoring/evidently/xgboost_drift_report.html"
#     xgb_report
#     xgb_report.save_html(str(report_path))
#     return HTMLResponse(content=report_path.read_text(), status_code=200)
        

# @app.get("/monitor/yolo", response_class=HTMLResponse)
# def yolo_report():
#     ref = BASE_DIR / "monitoring/evidently/yolo_reference_sample.csv"
#     prod = BASE_DIR / "monitoring/evidently/yolo_production_sample.csv"

#     if not ref.exists() or not prod.exists():
#         raise HTTPException(status_code=404, detail="Fichiers de monitoring YOLO manquants")

#     df_ref = pd.read_csv(ref)
#     df_prod = pd.read_csv(prod)

#     report = Report(metrics=[DataDriftPreset()])
#     report.run(reference_data=df_ref, current_data=df_prod)
#     report_path = BASE_DIR / "monitoring/evidently/yolo_drift_report.html"
#     report.save_html(str(report_path))
#     return HTMLResponse(content=report_path.read_text(), status_code=200)
