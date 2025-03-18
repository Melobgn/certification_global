from fastapi.testclient import TestClient
from api_ml.main_api_ml import app
import pytest

client = TestClient(app)  # Créer un client de test global

@pytest.mark.asyncio
async def test_predict():
    """Test de la prédiction avec un produit"""
    response = client.post(
        "/token",
        data={"username": "admin", "password": "password123"},
    )
    assert response.status_code == 200
    token = response.json()["access_token"]

    response = client.post(
        "/predict/",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "product_id": 1,
            "url": "https://www.exemple.com",
            "title": "arme de sport",
            "description": "fusil de chasse",
        },
    )

    assert response.status_code == 200
    assert "is_weapon_pred" in response.json()
    assert response.json()["is_weapon_pred"] in [0, 1]
