import pytest
import pickle
import numpy as np

@pytest.fixture
def load_model():
    """Charger le modèle XGBoost sauvegardé"""
    with open("model_ml/model_xgb.pkl", "rb") as f:
        saved_data = pickle.load(f)
    return saved_data["model"], saved_data["vectorizer"]

def test_model_prediction(load_model):
    """Vérifier que le modèle prédit correctement"""
    model, vectorizer = load_model
    sample_text = ["fusil automatique militaire"]
    X_vect = vectorizer.transform(sample_text)
    prediction = model.predict(X_vect)

    assert isinstance(prediction[0], np.int64), "La prédiction doit être un entier"
    assert prediction[0] in [0, 1], "La prédiction doit être 0 (non-weapon) ou 1 (weapon)"
