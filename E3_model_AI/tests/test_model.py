import pytest
import pickle
import numpy as np
import xgboost as xgb
from pathlib import Path
import os
import joblib

@pytest.fixture
def load_model():
    """Charger le modèle XGBoost sauvegardé et le vectorizer"""
    
    # Détecter GitHub Actions
    IS_CI = os.getenv("GITHUB_ACTIONS") == "true"

    # Définir le bon chemin en fonction de l'environnement
    if IS_CI:
        model_path = Path("E3_model_AI/model_ml/xgboost_weapon_classifier.pkl")
        vectorizer_path = Path("E3_model_AI/model_ml/tfidf_vectorizer.pkl")
    else:
        model_path = Path("model_ml/xgboost_weapon_classifier.pkl")
        vectorizer_path = Path("model_ml/tfidf_vectorizer.pkl")

    # Vérifier l'existence des fichiers
    if not model_path.exists():
        pytest.fail(f"❌ Modèle introuvable : {model_path}")
    if not vectorizer_path.exists():
        pytest.fail(f"❌ Vectorizer introuvable : {vectorizer_path}")

    # Charger le modèle XGBoost
    model = joblib.load(str(model_path))

    # Charger le vectorizer avec pickle
    vectorizer = joblib.load(vectorizer_path)

    return model, vectorizer

def test_model_prediction(load_model):
    """Vérifier que le modèle prédit correctement"""
    model, vectorizer = load_model
    sample_text = ["fusil automatique militaire"]

    # Transformer le texte en vecteur TF-IDF
    X_vect = vectorizer.transform(sample_text)

    prediction = model.predict(X_vect)

    assert prediction is not None
    assert prediction[0] in [0, 1]
