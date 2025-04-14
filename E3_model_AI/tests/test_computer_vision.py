import pytest
from ultralytics import YOLO
import cv2
import numpy as np
from pathlib import Path

# Charger le modèle YOLO pour le test
@pytest.fixture(scope="module")
def load_yolo_model():
    """Charger le modèle YOLO pour les tests."""
    model_path = Path("E3_model_AI/model_ml/best.pt")  # Vérifie le chemin exact
    if not model_path.exists():
        pytest.fail(f"Modèle YOLO introuvable : {model_path}")
    
    model = YOLO(str(model_path))
    return model

# Vérifier que le modèle YOLO se charge correctement
def test_yolo_model_load(load_yolo_model):
    """Vérifier que le modèle YOLO est bien chargé."""
    assert load_yolo_model is not None, "Le modèle YOLO n'a pas été chargé correctement"

# Tester YOLO avec une image d'exemple
def test_yolo_prediction(load_yolo_model):
    """Vérifier que YOLO effectue une prédiction sur une image valide."""
    test_image_path = "E3_model_AI/tests/test_image.jpg"  # Ajoute une image de test
    if not Path(test_image_path).exists():
        pytest.fail(f"Image de test introuvable : {test_image_path}")
    
    results = load_yolo_model.predict(source=test_image_path)

    # Vérifier que le modèle retourne des résultats
    assert results, "YOLO n'a retourné aucun résultat"
    
    # Vérifier que chaque détection a un score de confiance valide
    for r in results:
        assert hasattr(r, 'boxes'), "Les résultats YOLO ne contiennent pas de boîtes de détection"
        for box in r.boxes:
            conf = box.conf.item()
            assert 0 <= conf <= 1, f"Score de confiance invalide : {conf}"

# Vérifier qu’aucune erreur ne survient pendant l’exécution
def test_yolo_no_error(load_yolo_model):
    """S'assurer que YOLO ne renvoie pas d'erreur sur une image test."""
    test_image_path = "E3_model_AI/tests/test_image.jpg"
    if not Path(test_image_path).exists():
        pytest.fail(f"Image de test introuvable : {test_image_path}")
    
    try:
        results = load_yolo_model.predict(source=test_image_path)
    except Exception as e:
        pytest.fail(f"Erreur inattendue lors de l'exécution de YOLO : {e}")
