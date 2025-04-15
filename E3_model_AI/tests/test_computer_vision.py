import os
import pytest
from ultralytics import YOLO
from pathlib import Path

# Détecter GitHub Actions
IS_CI = os.getenv("GITHUB_ACTIONS") == "true"

# === FIXTURE ===
@pytest.fixture(scope="module")
def load_yolo_model():
    """Charger le modèle YOLO pour les tests."""
    model_path = Path("E3_model_AI/model_ml/best.pt") if IS_CI else Path("model_ml/best.pt")
    if not model_path.exists():
        pytest.fail(f"❌ Modèle YOLO introuvable : {model_path}")
    return YOLO(str(model_path))

@pytest.fixture(scope="module")
def test_image_path():
    """Fournir le chemin de l’image de test, selon l’environnement."""
    path = Path("E3_model_AI/tests/test_image.jpg") if IS_CI else Path("tests/test_image.jpg")
    if not path.exists():
        pytest.fail(f"❌ Image de test introuvable : {path}")
    return str(path)

# === TESTS ===
def test_yolo_model_load(load_yolo_model):
    assert load_yolo_model is not None, "❌ Le modèle YOLO n'a pas été chargé correctement"

def test_yolo_prediction(load_yolo_model, test_image_path):
    results = load_yolo_model.predict(source=test_image_path)
    assert results, "❌ YOLO n'a retourné aucun résultat"
    for r in results:
        assert hasattr(r, 'boxes'), "❌ Résultat sans boîtes de détection"
        for box in r.boxes:
            conf = box.conf.item()
            assert 0 <= conf <= 1, f"❌ Score de confiance invalide : {conf}"

def test_yolo_no_error(load_yolo_model, test_image_path):
    try:
        results = load_yolo_model.predict(source=test_image_path)
        assert results is not None, "Résultat YOLO vide"
    except Exception as e:
        pytest.fail(f"❌ Erreur inattendue lors de l'exécution de YOLO : {e}")
