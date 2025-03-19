from PIL import Image
import matplotlib.pyplot as plt
from ultralytics import YOLO
import cv2 
import numpy as np
import pandas as pd
import os
import shutil
import requests
import argparse
# from playwright.sync_api import sync_playwright

# Arguments de ligne de commande
parser = argparse.ArgumentParser(description="Pipeline de vision par ordinateur pour détecter des armes.")
parser.add_argument("--input", required=True, help="Chemin du fichier CSV d'entrée.")
parser.add_argument("--output", required=True, help="Chemin du fichier CSV de sortie.")
parser.add_argument("--model", default="./version5_best.pt", help="Chemin du modèle YOLO.")
parser.add_argument("--positive_output", default="positive_predictions.csv", help="Fichier pour les prédictions positives.")
parser.add_argument("--error_log", default="error_images_with_urls.csv", help="Fichier pour enregistrer les erreurs avec URLs.")
args = parser.parse_args()

# Charger les données
print(f"Chargement des données depuis {args.input}...")
df = pd.read_csv(args.input)
print(f"📌 Colonnes du CSV chargé : {df.columns.tolist()}")

# Filtrer pour les produits classés comme armes
df_weapon = df[df['is_weapon_pred'] == 1]

# Nettoyer et diviser la colonne "image" en liste d'images
def split_images(image_column):
    if isinstance(image_column, str):
        return [img.strip() for img in image_column.split(',') if img.strip()]
    return []

df_weapon['image_list'] = df_weapon['images_product'].apply(split_images)

# Normaliser les chemins d'images dans la liste d'images
df_weapon['image_list'] = df_weapon['image_list'].apply(lambda images: [img.strip().lower() for img in images])

# Supprimer les doublons uniquement au sein des listes d'une même URL
df_weapon['image_list'] = df_weapon['image_list'].apply(lambda x: list(set(x)))

# Initialiser YOLO
model = YOLO(args.model)

# Définir le seuil de confiance
CONFIDENCE_THRESHOLD = 0.6
results_data = []
positive_predictions = [] # Liste pour les prédictions positives avec URL et image
problematic_images_with_urls = [] # Liste unique pour capturer les images inaccessibles et les erreurs

# Vérifier l'accessibilité des URLs
def is_url_accessible(url):
    try:
        response = requests.head(url, timeout=5)
        return response.status_code == 200
    except Exception:
        return False

# Gestion des fichiers locaux pour les images
current_dir = os.getcwd() # Répertoire actuel
images_dir = os.path.join(current_dir, "images") # Répertoire cible

# Créer le répertoire 'images' s'il n'existe pas
if not os.path.exists(images_dir):
    os.makedirs(images_dir)
    print(f"Dossier '{images_dir}' créé.")
else:
    print(f"Dossier '{images_dir}' existe déjà.")

# Boucle principale : traitement de chaque image
for index, row in df_weapon.iterrows():
    images = row['image_list']
    product_data = {'url': row['url'], 'title': row['title'], 'description': row['description']}

    for image_path in images:
        # Vérifier si l'image est accessible
        if not is_url_accessible(image_path):
            print(f"Image inaccessible : {image_path}")
            problematic_images_with_urls.append({'url': row['url'], 'image': image_path, 'issue': 'Image inaccessible'})
            continue
 
        try:
            # Prédire avec YOLO
            results = model.predict(source=image_path)
            # Extraire le score de confiance maximal
            confidences = [
                box.conf.item()
                for r in results
                for box in r.boxes
                if box.conf.item() >= CONFIDENCE_THRESHOLD
            ]
            max_confidence = max(confidences) if confidences else None

            # Ajouter les résultats
            results_data.append({
                'url': product_data['url'],
                'title': product_data['title'],
                'description': product_data['description'],
                'image': image_path,
                'confidence_score': max_confidence
            })

            # Enregistrer les prédictions positives avec URL et image
            if max_confidence and max_confidence >= CONFIDENCE_THRESHOLD:
                positive_predictions.append({'url': product_data['url'], 'image': image_path})

        except Exception as e:
            print(f"Erreur lors du traitement de l'image {image_path}: {e}")
            problematic_images_with_urls.append({'url': row['url'], 'image': image_path, 'issue': f'Erreur : {str(e)}'})

# Convertir les résultats en DataFrame
results_df = pd.DataFrame(results_data)

# Normaliser les colonnes pour éviter les problèmes de doublons
results_df['url'] = results_df['url'].str.strip().str.lower()
results_df['title'] = results_df['title'].str.strip().str.lower()
results_df['description'] = results_df['description'].str.strip().str.lower()
results_df['image'] = results_df['image'].str.strip().str.lower()

# Supprimer les doublons dans le DataFrame final
results_df.drop_duplicates(subset=['url', 'title', 'description', 'image'], inplace=True)

# Sauvegarder les résultats
print(f"Sauvegarde des prédictions dans {args.output}...")
results_df.to_csv(args.output, index=False)

# Sauvegarder les images problématiques avec leurs URLs
if problematic_images_with_urls:
    problematic_df = pd.DataFrame(problematic_images_with_urls)
    problematic_df.to_csv(args.error_log, index=False)
    print(f"Chemins d'images problématiques enregistrés dans {args.error_log}.")
else:
    print("Aucune image problématique détectée.")

# Sauvegarder les prédictions positives avec leurs URLs
if positive_predictions:
    positive_df = pd.DataFrame(positive_predictions)
    positive_df.to_csv(args.positive_output, index=False)
    print(f"Résultats avec CV = 1 enregistrés dans {args.positive_output}.")
else:
    print("Aucune prédiction positive détectée.")

# Déplacer les fichiers locaux correspondants dans le dossier 'images'
valid_extensions = ('.png', '.jpg', '.jpeg', '.bmp', '.webp', '.svg')
for filename in os.listdir(current_dir):
    if filename.lower().endswith(valid_extensions):
        source_path = os.path.join(current_dir, filename)
        destination_path = os.path.join(images_dir, filename)
        try:
            shutil.move(source_path, destination_path)
            print(f"Image déplacée : {filename} -> {destination_path}")
        except Exception as e:
            print(f"Erreur lors du déplacement de {filename}: {e}")

print("Toutes les images ont été déplacées vers le dossier 'images'.")

# Résumé des résultats
print("Statistiques des prédictions YOLO :")
print(f"Nombre total d'images : {results_df['image'].nunique()}")
count_above_threshold = results_df[results_df['confidence_score'] > CONFIDENCE_THRESHOLD].shape[0]
print(f"Nombre d'images avec un score supérieur à {CONFIDENCE_THRESHOLD} : {count_above_threshold}")
print("Valeurs manquantes :")
print(results_df.isnull().sum())