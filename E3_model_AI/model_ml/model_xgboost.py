import xgboost as xgb
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix
import pandas as pd
import argparse
import os

# Arguments de ligne de commande
parser = argparse.ArgumentParser(description="Classification des produits avec XGBoost.")
parser.add_argument("--input", required=True, help="Chemin du fichier CSV d'entrée.")
parser.add_argument("--annotations", required=True, help="Chemin du fichier des annotations (Excel).")
parser.add_argument("--output", required=True, help="Chemin du fichier CSV de sortie.")
args = parser.parse_args()

# Vérification des fichiers
if not os.path.exists(args.input):
    raise FileNotFoundError(f"Fichier d'entrée introuvable : {args.input}")
if not os.path.exists(args.annotations):
    raise FileNotFoundError(f"Fichier des annotations introuvable : {args.annotations}")

# Charger le dataset complet
print(f"Chargement des données depuis {args.input}...")
df_full = pd.read_csv(args.input)

# Charger les annotations
print(f"Chargement des annotations depuis {args.annotations}...")
df_annotated = pd.read_excel(args.annotations)

# Identifier les données non annotées
df_unlabeled = df_full[~df_full['url'].isin(df_annotated['url'])]

# Préparer les données annotées
df_annotated['description'].fillna('', inplace=True)
df_annotated['title'].fillna('', inplace=True)
X = df_annotated[['description', 'title']]
y = df_annotated['is_weapon'].apply(lambda x: 1 if x == 'oui' else 0)

# Diviser en ensembles d'entraînement et de test
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, stratify=y, random_state=42)

# Fusionner les colonnes de texte
X_train_text = X_train['description'] + ' ' + X_train['title']
X_test_text = X_test['description'] + ' ' + X_test['title']

# Vectorisation TF-IDF
print("Vectorisation des textes avec TF-IDF...")
vectorizer = TfidfVectorizer(max_features=5000)
X_train_vect = vectorizer.fit_transform(X_train_text)
X_test_vect = vectorizer.transform(X_test_text)

# Calcul de scale_pos_weight pour gérer le déséquilibre des classes
scale_pos_weight = len(y_train) / sum(y_train == 1)

# Entraînement du modèle XGBoost
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

# Prédictions sur les données non annotées
print("Prédictions sur les données non annotées...")
df_unlabeled['description'].fillna('', inplace=True)
df_unlabeled['title'].fillna('', inplace=True)
X_unlabeled_text = df_unlabeled['description'] + ' ' + df_unlabeled['title']
X_unlabeled_vect = vectorizer.transform(X_unlabeled_text)
unlabeled_predictions = model.predict(X_unlabeled_vect)

# Ajouter les prédictions au dataset
df_unlabeled['is_weapon_pred'] = unlabeled_predictions

# Sauvegarder les résultats
print(f"Sauvegarde des prédictions dans {args.output}...")
df_unlabeled[['url', 'description', 'title', 'image', 'is_weapon_pred']].to_csv(args.output, index=False)

print(f"Prédictions enregistrées avec succès dans {args.output}.")
print(pd.Series(y_test).value_counts(normalize=True))