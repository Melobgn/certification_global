import streamlit as st
import requests
from bs4 import BeautifulSoup
import os
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv(".env")

API_URL = os.getenv("API_URL", "http://api:8000")

# Formulaire d'identifiants utilisateur
st.sidebar.title("🔐 Connexion à l'API")
username = st.sidebar.text_input("Nom d'utilisateur")
password = st.sidebar.text_input("Mot de passe", type="password")

# Fonction pour récupérer un token JWT
def get_token(api_url, username, password):
    response = requests.post(
        f"{api_url}/token",
        data={"username": username, "password": password},
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    if response.status_code == 200:
        return response.json()["access_token"]
    return None

# Authentifier au clic
if st.sidebar.button("Se connecter"):
    token = get_token(API_URL, username, password)
    if token:
        st.session_state["token"] = token
        st.sidebar.success("✅ Authentification réussie")
    else:
        st.sidebar.error("❌ Identifiants invalides")

# Bloquer l'app si non authentifié
token = st.session_state.get("token")
if not token:
    st.warning("Connectez-vous pour continuer.")
    st.stop()

HEADERS = {"Authorization": f"Bearer {token}"}

# Scraper les infos produit
def scrape_product_info(url):
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        title_tag = soup.find("meta", property="og:title") or soup.find("title")
        title = title_tag.get("content") if title_tag and title_tag.has_attr("content") else title_tag.get_text(strip=True) if title_tag else "Titre non trouvé"

        desc_tag = soup.find("meta", attrs={"name": "description"}) or soup.find("meta", property="og:description")
        description = desc_tag.get("content") if desc_tag else "Description non trouvée"

        imgs = [img.get("src") for img in soup.find_all("img") if img.get("src")]
        filtered_imgs = [i for i in imgs if i.endswith((".jpg", ".jpeg", ".png", ".webp"))]
        full_urls = [i if i.startswith("http") else requests.compat.urljoin(url, i) for i in filtered_imgs]

        return {
            "title": title,
            "description": description,
            "images": full_urls,
            "url": url
        }
    except Exception as e:
        return {"error": str(e)}

# Prediction texte
def predict_text(title, description, url):
    payload = {
        "title": title,
        "description": description,
        "product_id": 1,
        "url": url
    }
    response = requests.post(f"{API_URL}/predict/", json=payload, headers=HEADERS)
    if response.status_code == 200:
        return response.json()["is_weapon_pred"]
    return None

# Prediction image
def predict_image(image_url):
    response = requests.post(f"{API_URL}/predict_image/", json={"image_url": image_url}, headers=HEADERS)
    if response.status_code == 200:
        data = response.json()
        return data["is_weapon_cv"], data["confidence"]
    return 0, 0.0

# Interface utilisateur
st.title("🔍 Analyse d'un produit à partir d'une URL")

url = st.text_input("Colle ici une URL de produit")

if st.button("Analyser le produit"):
    with st.spinner("🔍 Analyse en cours..."):
        product = scrape_product_info(url)

        if "error" in product:
            st.error(f"Erreur de scraping : {product['error']}")
            st.stop()

        st.success("✅ Produit trouvé")
        st.write("### 📝 Titre :", product["title"])
        st.write("### 📄 Description :", product["description"])
        st.image(product["images"][:3], width=300)

        pred_text = predict_text(product["title"], product["description"], product["url"])
        if pred_text is not None:
            st.info(f"🧠 XGBoost : {'⚠️ Arme détectée' if pred_text else '✅ Non-armé'}")

        st.write("---")
        st.write("### 🖼️ Prédictions sur les images :")

        for img_url in product["images"][:3]:
            st.image(img_url, width=300)
            is_weapon_cv, conf = predict_image(img_url)
            label = "⚠️ Arme détectée" if is_weapon_cv else "✅ Non-armé"
            st.write(f"{label} — Confiance : {conf:.2f}")

        st.write("---")
        st.subheader("🎯 Verdict global")
        if pred_text == 1 or any(predict_image(img)[0] for img in product["images"][:3]):
            st.error("⚠️ Ce produit est potentiellement une arme !")
        else:
            st.success("✅ Aucun signal fort d'arme détecté.")

