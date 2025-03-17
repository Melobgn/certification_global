import pandas as pd
import pickle
import argparse
import os

# Arguments de ligne de commande
parser = argparse.ArgumentParser(description="Prédictions avec le modèle XGBoost.")
parser.add_argument("--input", required=True, help="Chemin du fichier CSV d'entrée.")
parser.add_argument("--annotations", required=True, help="Chemin du fichier des annotations (Excel).")
parser.add_argument("--model", required=True, help="Chemin du fichier modèle sauvegardé (.pkl).")
parser.add_argument("--output", required=True, help="Chemin du fichier CSV de sortie.")
args = parser.parse_args()

# Vérification des fichiers
if not os.path.exists(args.input):
    raise FileNotFoundError(f"Fichier d'entrée introuvable : {args.input}")
if not os.path.exists(args.annotations):
    raise FileNotFoundError(f"Fichier des annotations introuvable : {args.annotations}")
if not os.path.exists(args.model):
    raise FileNotFoundError(f"Modèle introuvable : {args.model}")

# Charger le modèle et le vectorizer
print(f"Chargement du modèle depuis {args.model}...")
with open(args.model, "rb") as f:
    saved_data = pickle.load(f)
    model = saved_data["model"]
    vectorizer = saved_data["vectorizer"]

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
X_unlabeled_vect = vectorizer.transform(X_unlabeled_text)

# Prédictions
print("Prédictions sur les données non annotées...")
df_unlabeled['is_weapon_pred'] = model.predict(X_unlabeled_vect)

# Sauvegarde des résultats
df_unlabeled[['product_id', 'url', 'description', 'title', 'is_weapon_pred']].to_csv(args.output, index=False)
print(f"✅ Prédictions enregistrées dans {args.output}.")
