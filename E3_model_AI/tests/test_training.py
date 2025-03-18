import pytest
import xgboost as xgb
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.datasets import make_classification

@pytest.fixture
def training_data():
    """Générer un jeu de données synthétique"""
    X, y = make_classification(n_samples=100, n_features=20, random_state=42)
    return X, y

def test_model_training(training_data):
    """Vérifier que le modèle XGBoost s'entraîne correctement"""
    X, y = training_data
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)

    model = xgb.XGBClassifier()
    model.fit(X_train, y_train)

    assert model is not None, "Le modèle XGBoost doit être entraîné"
    assert model.predict(X_test).shape == y_test.shape, "Les prédictions doivent avoir la même taille que les labels"
