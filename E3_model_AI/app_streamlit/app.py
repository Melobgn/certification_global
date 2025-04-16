import streamlit as st
import requests
from bs4 import BeautifulSoup
import os
from dotenv import load_dotenv
import pandas as pd

# Charger les variables d'environnement
load_dotenv(".env")

API_URL = os.getenv("API_URL", "http://api:8000")

# Formulaire d'identifiants utilisateur
st.sidebar.title("🔐 Connexion à l'API")
username = st.sidebar.text_input("Nom d'utilisateur")
password = st.sidebar.text_input("Mot de passe", type="password")

def get_token(api_url, username, password):
    response = requests.post(
        f"{api_url}/token",
        data={"username": username, "password": password},
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    if response.status_code == 200:
        return response.json()["access_token"]
    return None

if st.sidebar.button("Se connecter"):
    token = get_token(API_URL, username, password)
    if token:
        st.session_state["token"] = token
        st.sidebar.success("✅ Authentification réussie")
    else:
        st.sidebar.error("❌ Identifiants invalides")

token = st.session_state.get("token")
if not token:
    st.warning("Connectez-vous pour continuer.")
    st.stop()

HEADERS = {"Authorization": f"Bearer {token}"}

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

def predict_image(image_url):
    response = requests.post(f"{API_URL}/predict_image/", json={"image_url": image_url}, headers=HEADERS)
    if response.status_code == 200:
        data = response.json()
        return data["is_weapon_cv"], data["confidence"]
    return 0, 0.0

# Onglets
tabs = st.tabs(["🔍 Analyse", "📊 Monitoring"])

# ========== Onglet 1 : Analyse ==========
with tabs[0]:
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


                # Historique des analyses
    st.write("---")
    st.subheader("🕓 Historique des produits analysés")

    if "history" not in st.session_state:
        st.session_state["history"] = []

    # Ajouter à l'historique si l'analyse vient d'être faite
    if url and "title" in product:
        st.session_state["history"].append({
            "URL": product["url"],
            "Titre": product["title"],
            "Description": product["description"],
            "XGBoost": "Arme" if pred_text else "Non-armé",
            "YOLO": "Arme" if any(predict_image(img)[0] for img in product["images"][:3]) else "Non-armé"
        })

    # Affichage du tableau d'historique
    if st.session_state["history"]:
        df_hist = pd.DataFrame(st.session_state["history"])
        st.dataframe(df_hist)

        # Bouton export CSV
        csv = df_hist.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="📁 Exporter l'historique en CSV",
            data=csv,
            file_name="historique_predictions.csv",
            mime="text/csv"
        )


# ========== Onglet 2 : Monitoring ==========

PROM_URL = "http://prometheus:9090"

def get_metric_from_prometheus(metric_name):
    try:
        response = requests.get(f"{PROM_URL}/api/v1/query", params={"query": metric_name})
        if response.status_code == 200:
            result = response.json()["data"]["result"]
            if result:
                return float(result[0]["value"][1])
        return None
    except Exception as e:
        st.error(f"Erreur Prometheus: {e}")
        return None
    
with tabs[1]:
    st.title("📈 Monitoring des modèles")
    
    xgb_score = get_metric_from_prometheus("xgboost_data_drift")
    yolo_score = get_metric_from_prometheus("yolo_data_drift")

    if xgb_score is not None:
        if xgb_score > 0.3:
            st.error(f"⚠️ Drift XGBoost élevé : {xgb_score:.2%}")
        else:
            st.success(f"✅ Drift XGBoost : {xgb_score:.2%}")
    else:
        st.warning("Aucune donnée XGBoost")

    if yolo_score is not None:
        if yolo_score > 0.3:
            st.error(f"⚠️ Drift YOLO élevé : {yolo_score:.2%}")
        else:
            st.success(f"✅ Drift YOLO : {yolo_score:.2%}")
    else:
        st.warning("Aucune donnée YOLO")

    st.markdown("[📊 Ouvrir le dashboard Grafana](http://localhost:3000)")



# import streamlit as st
# import requests
# from bs4 import BeautifulSoup
# import os
# from dotenv import load_dotenv

# # Charger les variables d'environnement
# load_dotenv(".env")

# API_URL = os.getenv("API_URL", "http://api:8000")

# # Formulaire d'identifiants utilisateur
# st.sidebar.title("🔐 Connexion à l'API")
# username = st.sidebar.text_input("Nom d'utilisateur")
# password = st.sidebar.text_input("Mot de passe", type="password")

# # Fonction pour récupérer un token JWT
# def get_token(api_url, username, password):
#     response = requests.post(
#         f"{api_url}/token",
#         data={"username": username, "password": password},
#         headers={"Content-Type": "application/x-www-form-urlencoded"}
#     )
#     if response.status_code == 200:
#         return response.json()["access_token"]
#     return None

# # Authentifier au clic
# if st.sidebar.button("Se connecter"):
#     token = get_token(API_URL, username, password)
#     if token:
#         st.session_state["token"] = token
#         st.sidebar.success("✅ Authentification réussie")
#     else:
#         st.sidebar.error("❌ Identifiants invalides")

# # Bloquer l'app si non authentifié
# token = st.session_state.get("token")
# if not token:
#     st.warning("Connectez-vous pour continuer.")
#     st.stop()

# HEADERS = {"Authorization": f"Bearer {token}"}

# # Scraper les infos produit
# def scrape_product_info(url):
#     try:
#         response = requests.get(url, timeout=10)
#         response.raise_for_status()
#         soup = BeautifulSoup(response.text, "html.parser")

#         title_tag = soup.find("meta", property="og:title") or soup.find("title")
#         title = title_tag.get("content") if title_tag and title_tag.has_attr("content") else title_tag.get_text(strip=True) if title_tag else "Titre non trouvé"

#         desc_tag = soup.find("meta", attrs={"name": "description"}) or soup.find("meta", property="og:description")
#         description = desc_tag.get("content") if desc_tag else "Description non trouvée"

#         imgs = [img.get("src") for img in soup.find_all("img") if img.get("src")]
#         filtered_imgs = [i for i in imgs if i.endswith((".jpg", ".jpeg", ".png", ".webp"))]
#         full_urls = [i if i.startswith("http") else requests.compat.urljoin(url, i) for i in filtered_imgs]

#         return {
#             "title": title,
#             "description": description,
#             "images": full_urls,
#             "url": url
#         }
#     except Exception as e:
#         return {"error": str(e)}

# # Prediction texte
# def predict_text(title, description, url):
#     payload = {
#         "title": title,
#         "description": description,
#         "product_id": 1,
#         "url": url
#     }
#     response = requests.post(f"{API_URL}/predict/", json=payload, headers=HEADERS)
#     if response.status_code == 200:
#         return response.json()["is_weapon_pred"]
#     return None

# # Prediction image
# def predict_image(image_url):
#     response = requests.post(f"{API_URL}/predict_image/", json={"image_url": image_url}, headers=HEADERS)
#     if response.status_code == 200:
#         data = response.json()
#         return data["is_weapon_cv"], data["confidence"]
#     return 0, 0.0

# # Interface utilisateur
# st.title("🔍 Analyse d'un produit à partir d'une URL")

# url = st.text_input("Colle ici une URL de produit")

# if st.button("Analyser le produit"):
#     with st.spinner("🔍 Analyse en cours..."):
#         product = scrape_product_info(url)

#         if "error" in product:
#             st.error(f"Erreur de scraping : {product['error']}")
#             st.stop()

#         st.success("✅ Produit trouvé")
#         st.write("### 📝 Titre :", product["title"])
#         st.write("### 📄 Description :", product["description"])
#         st.image(product["images"][:3], width=300)

#         pred_text = predict_text(product["title"], product["description"], product["url"])
#         if pred_text is not None:
#             st.info(f"🧠 XGBoost : {'⚠️ Arme détectée' if pred_text else '✅ Non-armé'}")

#         st.write("---")
#         st.write("### 🖼️ Prédictions sur les images :")

#         for img_url in product["images"][:3]:
#             st.image(img_url, width=300)
#             is_weapon_cv, conf = predict_image(img_url)
#             label = "⚠️ Arme détectée" if is_weapon_cv else "✅ Non-armé"
#             st.write(f"{label} — Confiance : {conf:.2f}")

#         st.write("---")
#         st.subheader("🎯 Verdict global")
#         if pred_text == 1 or any(predict_image(img)[0] for img in product["images"][:3]):
#             st.error("⚠️ Ce produit est potentiellement une arme !")
#         else:
#             st.success("✅ Aucun signal fort d'arme détecté.")

