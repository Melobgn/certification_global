from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from datetime import timedelta
import pickle
import os
from pathlib import Path
from dotenv import load_dotenv
from .auth import get_current_user, create_access_token, authenticate_user
from .models_api_ml import Product, ProductWithPrediction, Token
import xgboost as xgb

# Charger le fichier .env
env_path = Path(__file__).parent / ".env"
load_dotenv(env_path)

# Charger le modèle XGBoost et le vectorizer TF-IDF
# MODEL_PATH = "/app/model_ml/model_xgb.pkl"
MODEL_PATH = Path("/app/model_ml/model_xgb.json")
VECTORIZER_PATH = Path("/app/model_ml/vectorizer.pkl")

if not os.path.exists(MODEL_PATH):
    raise FileNotFoundError("Le modèle XGBoost n'a pas été trouvé.")

# Charger le modèle XGBoost
model = xgb.Booster()
model.load_model(str(MODEL_PATH))

# Charger le vectorizer séparément
with open(VECTORIZER_PATH, "rb") as f:
    vectorizer = pickle.load(f)

# Initialisation de l'API
app = FastAPI(
    title="API XGBoost - Détection d'Armes",
    description="""
    Cette API permet de classifier des produits d'e-commerce pour détecter 
    ceux qui sont susceptibles d'être des armes.""",
    version="1.0.0"
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
# PREDICTION AVEC XGBOOST
# ==============================
@app.post("/predict/", response_model=ProductWithPrediction)
def predict(data: Product, user: dict = Depends(get_current_user)):
    """ Prédiction XGBoost sécurisée par token JWT """
    text = data.description + " " + data.title
    text_vect = vectorizer.transform([text])
    prediction = model.predict(xgb.DMatrix(text_vect))[0]  # XGBoost utilise DMatrix pour les prédictions

    return ProductWithPrediction(
        product_id=data.product_id,
        url=data.url,
        title=data.title,
        description=data.description,
        is_weapon_pred=int(prediction)
    )
