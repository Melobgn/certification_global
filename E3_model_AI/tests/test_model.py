import pytest
import pickle
import numpy as np
import xgboost as xgb
from pathlib import Path
import os

@pytest.fixture
def load_model():
    """Charger le modèle XGBoost sauvegardé et le vectorizer"""
    
    # Détecter GitHub Actions
    IS_CI = os.getenv("GITHUB_ACTIONS") == "true"

    # Définir le bon chemin en fonction de l'environnement
    if IS_CI:
        model_path = Path("E3_model_AI/model_ml/model_xgb.json")
        vectorizer_path = Path("E3_model_AI/model_ml/vectorizer.pkl")
    else:
        model_path = Path("model_ml/model_xgb.json")
        vectorizer_path = Path("model_ml/vectorizer.pkl")

    # Vérifier l'existence des fichiers
    if not model_path.exists():
        pytest.fail(f"❌ Modèle introuvable : {model_path}")
    if not vectorizer_path.exists():
        pytest.fail(f"❌ Vectorizer introuvable : {vectorizer_path}")

    # Charger le modèle XGBoost
    model = xgb.Booster()
    model.load_model(str(model_path))

    # Charger le vectorizer avec pickle
    with open(vectorizer_path, "rb") as f:
        vectorizer = pickle.load(f)

    return model, vectorizer

def test_model_prediction(load_model):
    """Vérifier que le modèle prédit correctement"""
    model, vectorizer = load_model
    sample_text = ["fusil automatique militaire"]

    # Transformer le texte en vecteur TF-IDF
    X_vect = vectorizer.transform(sample_text)

    # Convertir en format DMatrix pour XGBoost
    X_dmatrix = xgb.DMatrix(X_vect)

    # Prédiction
    prediction = model.predict(X_dmatrix)
    predicted_class = int(round(prediction[0]))  # Convertir en entier 0 ou 1

    # Vérifications
    assert isinstance(predicted_class, int), "La prédiction doit être un entier"
    assert predicted_class in [0, 1], "La prédiction doit être 0 (non-weapon) ou 1 (weapon)"
