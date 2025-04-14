from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
import pandas as pd
import argparse
import os
import xgboost as xgb
import joblib 

# === ARGUMENTS EN LIGNE DE COMMANDE ===
parser = argparse.ArgumentParser(description="Classification des produits avec XGBoost (split par site, filtrage strict).")
parser.add_argument("--input", required=True, help="Chemin du fichier CSV d'entrée.")
parser.add_argument("--annotations", required=True, help="Chemin du fichier des annotations (Excel).")
parser.add_argument("--output", required=True, help="Chemin du fichier CSV de sortie.")
args = parser.parse_args()

# === VÉRIFICATION DES FICHIERS ===
if not os.path.exists(args.input):
    raise FileNotFoundError(f"Fichier d'entrée introuvable : {args.input}")
if not os.path.exists(args.annotations):
    raise FileNotFoundError(f"Fichier des annotations introuvable : {args.annotations}")

# === CHARGEMENT DES DONNÉES ===
print(f"Chargement des données depuis {args.input}...")
df_full = pd.read_csv(args.input)

print(f"Chargement des annotations depuis {args.annotations}...")
df_annotated = pd.read_excel(args.annotations)

# === EXTRACTION DU SITE ===
def extract_site(url):
    try:
        parts = url.split('/')
        if len(parts) >= 3:
            return parts[2]
        else:
            return 'site_invalide'
    except:
        return 'site_invalide'

df_annotated['site'] = df_annotated['url'].apply(extract_site)
df_full['site'] = df_full['url'].apply(extract_site)


# === SPLIT PAR SITE ENTRE TRAIN ET TEST ===
unique_sites = df_annotated['site'].unique()
train_sites, test_sites = train_test_split(unique_sites, test_size=0.2, random_state=42)

df_train = df_annotated[df_annotated['site'].isin(train_sites)].copy()
df_test = df_annotated[df_annotated['site'].isin(test_sites)].copy()

# === PRÉPARATION DES DONNÉES ===
for df in [df_train, df_test]:
    df['description'].fillna('', inplace=True)
    df['title'].fillna('', inplace=True)

X_train_text = df_train['description'] + ' ' + df_train['title']
X_test_text = df_test['description'] + ' ' + df_test['title']
y_train = df_train['is_weapon'].apply(lambda x: 1 if x == 'oui' else 0)
y_test = df_test['is_weapon'].apply(lambda x: 1 if x == 'oui' else 0)

# === TF-IDF ===
print("Vectorisation des textes avec TF-IDF...")
vectorizer = TfidfVectorizer(max_features=5000)
X_train_vect = vectorizer.fit_transform(X_train_text)
X_test_vect = vectorizer.transform(X_test_text)

# === XGBOOST ===
scale_pos_weight = len(y_train) / sum(y_train == 1)

print("Entraînement du modèle XGBoost...")
model = xgb.XGBClassifier(
    scale_pos_weight=scale_pos_weight,
    use_label_encoder=False,
    eval_metric='logloss',
    random_state=42
)
model.fit(X_train_vect, y_train)

# === EVALUATION ===
print("Evaluation du modèle sur des sites jamais vus...")
y_pred = model.predict(X_test_vect)
print(classification_report(y_test, y_pred))

# === ENREGISTREMENT DU MODELE ET VECTORIZER ===
print("Enregistrement du modèle et du vectorizer...")
joblib.dump(model, "xgboost_weapon_classifier.pkl")
joblib.dump(vectorizer, "tfidf_vectorizer.pkl")
print("Modèle et vectorizer enregistrés avec succès.")

# === FILTRAGE DES DONNEES NON ANNOTÉES ===
print("Filtrage des données non annotées pour prédiction...")
urls_annotees = set(df_annotated['url'])
sites_train = set(df_train['site'])
sites_test = set(df_test['site'])
sites_vus = sites_train.union(sites_test)

# df_unlabeled = df_full[
#     ~df_full['url'].isin(urls_annotees) &
#     ~df_full['site'].isin(sites_vus)
# ].copy()

df_unlabeled = df_full[
    ~df_full['url'].isin(urls_annotees)
].copy()

df_unlabeled['description'].fillna('', inplace=True)
df_unlabeled['title'].fillna('', inplace=True)
X_unlabeled_text = df_unlabeled['description'] + ' ' + df_unlabeled['title']
X_unlabeled_vect = vectorizer.transform(X_unlabeled_text)

# === PREDICTIONS ===
print("Prédictions sur les données de sites inconnus...")
df_unlabeled['is_weapon_pred'] = model.predict(X_unlabeled_vect)

# === SAUVEGARDE ===
print(f"Sauvegarde des prédictions dans {args.output}...")
df_unlabeled[['url', 'description', 'title', 'product_id', 'is_weapon_pred']].to_csv(args.output, index=False)

print("Prédictions enregistrées avec succès.")
print("Répartition des classes dans le set de test :")
print(pd.Series(y_test).value_counts(normalize=True))