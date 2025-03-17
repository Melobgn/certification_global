import xgboost as xgb
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
import pandas as pd
import argparse
import os
import pickle

# Arguments de ligne de commande
parser = argparse.ArgumentParser(description="Entraînement du modèle XGBoost pour la détection d'armes.")
parser.add_argument("--input", required=True, help="Chemin du fichier CSV d'entrée.")
parser.add_argument("--annotations", required=True, help="Chemin du fichier des annotations (Excel).")
parser.add_argument("--model_output", required=True, help="Chemin du fichier modèle sauvegardé (.pkl).")
args = parser.parse_args()

# Vérification des fichiers
if not os.path.exists(args.input):
    raise FileNotFoundError(f"Fichier d'entrée introuvable : {args.input}")
if not os.path.exists(args.annotations):
    raise FileNotFoundError(f"Fichier des annotations introuvable : {args.annotations}")

# Charger les données annotées
print(f"Chargement des annotations depuis {args.annotations}...")
df_annotated = pd.read_excel(args.annotations)
df_annotated['description'].fillna('', inplace=True)
df_annotated['title'].fillna('', inplace=True)

# Préparer X et y
X = df_annotated[['description', 'title']]
y = df_annotated['is_weapon'].apply(lambda x: 1 if x == 'oui' else 0)

# Diviser en train/test
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, stratify=y, random_state=42)

# Fusionner description et titre
X_train_text = X_train['description'] + ' ' + X_train['title']
X_test_text = X_test['description'] + ' ' + X_test['title']

# Vectorisation TF-IDF
print("Vectorisation des textes avec TF-IDF...")
vectorizer = TfidfVectorizer(max_features=5000)
X_train_vect = vectorizer.fit_transform(X_train_text)
X_test_vect = vectorizer.transform(X_test_text)

# Calcul du poids de classe
scale_pos_weight = len(y_train) / sum(y_train == 1)

# Entraînement du modèle
print("Entraînement du modèle XGBoost...")
model = xgb.XGBClassifier(
    scale_pos_weight=scale_pos_weight,
    use_label_encoder=False,
    eval_metric='logloss',
    random_state=42
)
model.fit(X_train_vect, y_train)

# Évaluation
print("Évaluation du modèle...")
y_pred = model.predict(X_test_vect)
print(classification_report(y_test, y_pred))

# Sauvegarde du modèle et du vectorizer
with open(args.model_output, "wb") as f:
    pickle.dump({"model": model, "vectorizer": vectorizer}, f)

print(f"Modèle sauvegardé sous {args.model_output}.")
