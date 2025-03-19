import sqlite3
import pandas as pd
import argparse
import os

# 📌 Définition des arguments du script
parser = argparse.ArgumentParser(description="Ajout des URLs d'images aux prédictions XGBoost.")
parser.add_argument("--input", required=True, help="Chemin du fichier CSV d'entrée (prédictions XGBoost).")
parser.add_argument("--db", required=True, help="Chemin vers la base de données SQLite.")
parser.add_argument("--output", required=True, help="Chemin du fichier de sortie avec les images.")
args = parser.parse_args()

# 🔍 Vérification des fichiers d'entrée
if not os.path.exists(args.input):
    raise FileNotFoundError(f"❌ Fichier d'entrée introuvable : {args.input}")
if not os.path.exists(args.db):
    raise FileNotFoundError(f"❌ Base de données SQLite introuvable : {args.db}")

# 📌 Charger le CSV des prédictions
df_predictions = pd.read_csv(args.input)

# 📡 Connexion à la base SQLite
conn = sqlite3.connect(args.db)

# 🖼️ Récupérer les URLs des images pour chaque product_id
query = """
    SELECT product_id, GROUP_CONCAT(image_url) as images_product
    FROM product_image
    WHERE product_id IN ({})
    GROUP BY product_id;
""".format(",".join(map(str, df_predictions["product_id"].unique())))

df_images = pd.read_sql_query(query, conn)

# 🔄 Fermer la connexion
conn.close()

# 📌 Fusionner les données
df_final = df_predictions.merge(df_images, on="product_id", how="left")

# 📝 Sauvegarde du fichier final
df_final.to_csv(args.output, index=False)

print(f"✅ Fusion terminée ! Fichier enregistré sous {args.output}")
