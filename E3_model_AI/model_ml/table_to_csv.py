import sqlite3
import pandas as pd

# 🔹 Connexion à la base de données SQLite
DB_PATH = "/home/utilisateur/Documents/Certification/certification_global/E1_gestion_donnees/database/weapon_detection.db"  # Assure-toi que le fichier existe
conn = sqlite3.connect(DB_PATH)

# 🔹 Charger la table "product" dans un DataFrame
df = pd.read_sql("SELECT * FROM product;", conn)

# 🔹 Fermer la connexion à la base
conn.close()

# 🔹 Afficher les premières lignes pour vérifier
print(df.head())

# 🔹 Sauvegarde en CSV pour XGBoost
df.to_csv("products_xgboost.csv", index=False)
print("Données sauvegardées sous 'products_xgboost.csv'")
