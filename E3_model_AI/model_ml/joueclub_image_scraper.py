from playwright.sync_api import sync_playwright
import pandas as pd
import time

# Charger les URLs depuis error_images.csv
input_csv = "./error_images_fixed.csv"
output_csv = "./fixed_images_playwright.csv"

df = pd.read_csv(input_csv)
df_fixed = []

# Fonction pour récupérer les images d'un produit JouéClub
def fetch_images(url):
    images_found = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)  # False pour tester visuellement
        page = browser.new_page()
        
        try:
            print(f"🔍 Chargement de {url} avec Playwright...")
            page.goto(url, timeout=15000)  # Timeout augmenté à 15s
            page.wait_for_load_state("networkidle")
            time.sleep(3)  # Pause pour charger les images dynamiques
            
            # Extraire toutes les images des balises <img> dans ".product__imageLink.visible"
            images = page.query_selector_all(".product__imageLink.visible img")
            
            for img in images:
                src = img.get_attribute("src")
                if src and src.startswith("http"):
                    images_found.append(src)

        except Exception as e:
            print(f"❌ Erreur sur {url} : {e}")
        finally:
            browser.close()
    
    return images_found

# Boucle sur les URLs à récupérer
for index, row in df.iterrows():
    url = row["url"]
    new_images = fetch_images(url)

    if new_images:
        for img_url in new_images:
            df_fixed.append({"url": url, "image": img_url, "issue": "Récupéré via Playwright"})
    else:
        df_fixed.append({"url": url, "image": None, "issue": "Aucune image trouvée"})

# Sauvegarder les nouvelles images
df_fixed = pd.DataFrame(df_fixed)
df_fixed.to_csv(output_csv, index=False)
print(f"✅ Images récupérées avec succès via Playwright et enregistrées dans {output_csv}")
