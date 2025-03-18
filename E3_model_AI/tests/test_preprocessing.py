import pytest
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer

@pytest.fixture
def sample_data():
    """Données d'exemple pour tester la vectorisation"""
    return pd.DataFrame({
        "description": ["fusil de chasse", "jouet enfant", "pistolet à eau"],
        "title": ["arme", "jeu", "jouet"]
    })

def test_tfidf_vectorization(sample_data):
    """Test si la vectorisation TF-IDF fonctionne correctement"""
    vectorizer = TfidfVectorizer()
    combined_text = sample_data["description"] + " " + sample_data["title"]
    X_transformed = vectorizer.fit_transform(combined_text)

    assert X_transformed.shape[0] == len(sample_data), "Le nombre de lignes après transformation doit être correct"
