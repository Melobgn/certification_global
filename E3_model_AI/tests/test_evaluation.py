import pytest
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
import numpy as np

@pytest.fixture
def sample_predictions():
    """Données de test pour évaluer le modèle"""
    y_true = np.array([1, 0, 1, 1, 0, 0, 1])
    y_pred = np.array([1, 0, 1, 0, 0, 1, 1])
    return y_true, y_pred

def test_evaluation_metrics(sample_predictions):
    """Vérifier que les métriques d'évaluation sont correctement calculées"""
    y_true, y_pred = sample_predictions

    assert 0 <= accuracy_score(y_true, y_pred) <= 1, "L'accuracy doit être entre 0 et 1"
    assert 0 <= precision_score(y_true, y_pred) <= 1, "La précision doit être entre 0 et 1"
    assert 0 <= recall_score(y_true, y_pred) <= 1, "Le rappel doit être entre 0 et 1"
    assert 0 <= f1_score(y_true, y_pred) <= 1, "Le F1-score doit être entre 0 et 1"
