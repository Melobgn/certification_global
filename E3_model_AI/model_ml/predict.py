import pandas as pd
import xgboost as xgb
import pickle
import argparse
import os

# Arguments de ligne de commande
parser = argparse.ArgumentParser(description="Prédictions avec le modèle XGBoost.")
parser.add_argument("--input", required=True, help="Chemin du fichier CSV d'entrée.")
parser.add_argument("--annotations", required=True, help="Chemin du fichier des annotations (Excel).")
parser.add_argument("--model", required=True, help="Chemin du fichier modèle sauvegardé (.json).")
parser.add_argument("--vectorizer", required=True, help="Chemin du fichier vectorizer sauvegardé (.pkl).")
parser.add_argument("--output", required=True, help="Chemin du fichier CSV de sortie.")
args = parser.parse_args()

# Vérification des fichiers
if not os.path.exists(args.input):
    raise FileNotFoundError(f"Fichier d'entrée introuvable : {args.input}")
if not os.path.exists(args.annotations):
    raise FileNotFoundError(f"Fichier des annotations introuvable : {args.annotations}")
if not os.path.exists(args.model):
    raise FileNotFoundError(f"Modèle introuvable : {args.model}")
if not os.path.exists(args.vectorizer):
    raise FileNotFoundError(f"Vectorizer introuvable : {args.vectorizer}")

# Charger le modèle XGBoost
print(f"🔄 Chargement du modèle depuis {args.model}...")
model = xgb.Booster()
model.load_model(args.model)

# Charger le vectorizer
print(f"🔄 Chargement du vectorizer depuis {args.vectorizer}...")
with open(args.vectorizer, "rb") as f:
    vectorizer = pickle.load(f)

# Charger les datasets
df_full = pd.read_csv(args.input)
df_annotated = pd.read_excel(args.annotations)

# Identifier les données non annotées
df_unlabeled = df_full[~df_full['url'].isin(df_annotated['url'])]

# Préparer les données non annotées
df_unlabeled['description'].fillna('', inplace=True)
df_unlabeled['title'].fillna('', inplace=True)
X_unlabeled_text = df_unlabeled['description'] + ' ' + df_unlabeled['title']

# Vectorisation
print("🔄 Vectorisation des données...")
X_unlabeled_vect = vectorizer.transform(X_unlabeled_text)

# Conversion en DMatrix pour XGBoost
X_unlabeled_dmatrix = xgb.DMatrix(X_unlabeled_vect)

# Prédictions
print("🔍 Prédictions sur les données non annotées...")
df_unlabeled['is_weapon_pred'] = model.predict(X_unlabeled_dmatrix).astype(int)  # Assure un format entier

# 🔥 Ajout de la règle basée sur 'generique_name' : si renseigné, forcer à 1
if 'generic_name' in df_unlabeled.columns:
    df_unlabeled.loc[df_unlabeled["generic_name"].notna(), "is_weapon_pred"] = 1
else:
    print("⚠️ Attention : La colonne 'generic_name' est absente du dataset. Aucune correction appliquée.")

# Vérification des résultats après correction
print("📊 Répartition des prédictions après correction :")
print(df_unlabeled["is_weapon_pred"].value_counts())

# Sauvegarde des résultats mis à jour
df_unlabeled[['product_id', 'url', 'description', 'title', 'generic_name', 'is_weapon_pred']].to_csv(args.output, index=False)
print(f"✅ Prédictions mises à jour enregistrées dans {args.output}.")
