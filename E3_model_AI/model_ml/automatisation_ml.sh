#!/bin/bash

# Définition des chemins des fichiers
SCRAPING_OUTPUT="/home/utilisateur/Documents/Certification/certification_global/E3_model_AI/model_ml/products_xgboost.csv"
ANNOTATIONS_FILE="/home/utilisateur/Documents/Certification/certification_global/E3_model_AI/model_ml/dataset_annotation_update.xlsx"
XGBOOST_OUTPUT="/home/utilisateur/Documents/Certification/certification_global/E3_model_AI/model_ml/predictions_xgboost.csv"
VISION_OUTPUT="/home/utilisateur/Documents/Certification/certification_global/E3_model_AI/model_ml/predictions_computer_vision.csv"
YOLO_MODEL="/home/utilisateur/Documents/Certification/certification_global/E3_model_AI/model_ml/best.pt" # Modèle YOLO pour la vision
VISION_DIR="/home/utilisateur/Documents/Certification/certification_global/E3_model_AI/model_ml/vision_results" # Répertoire des résultats de vision
XGBOOST_ENRICHED_OUTPUT="/home/utilisateur/Documents/Certification/certification_global/E3_model_AI/model_ml/predictions_xgboost_with_images.csv"

# Vérifier que le fichier concaténé existe
if [ ! -f "$SCRAPING_OUTPUT" ]; then
    echo "Erreur : Fichier $SCRAPING_OUTPUT introuvable après le scraping."
    exit 1
fi

# Vérifier que le fichier d'annotations existe
if [ ! -f "$ANNOTATIONS_FILE" ]; then
    echo "Erreur : Fichier $ANNOTATIONS_FILE introuvable."
    exit 1
fi


# Étape 2 : Exécuter la prédiction avec le modèle XGBoost
echo "🔍 Lancement des prédictions XGBoost..."
python3 /home/utilisateur/Documents/Certification/certification_global/E3_model_AI/model_ml/test_classification_model.py \
    --input "$SCRAPING_OUTPUT" \
    --annotations "$ANNOTATIONS_FILE" \
    --output "$XGBOOST_OUTPUT"

if [ $? -ne 0 ]; then
    echo "Erreur lors de l'exécution des prédictions XGBoost. Arrêt du pipeline."
    exit 1
fi
echo "✅ Prédictions XGBoost terminées avec succès. Résultats dans $XGBOOST_OUTPUT."

# Vérifier que le fichier des prédictions a bien été généré
if [ ! -f "$XGBOOST_OUTPUT" ]; then
    echo "Erreur : Fichier $XGBOOST_OUTPUT introuvable après l'exécution de XGBoost."
    exit 1
fi

echo "Pipeline XGBoost terminé avec succès."

# Étape 2.5 : Ajout des URLs des images aux prédictions
echo "🔍 Ajout des URLs des images aux prédictions..."
python3 /home/utilisateur/Documents/Certification/certification_global/E3_model_AI/model_ml/images_to_predictions.py \
    --input "$XGBOOST_OUTPUT" \
    --db "/home/utilisateur/Documents/Certification/certification_global/E1_gestion_donnees/database/weapon_detection.db" \
    --output "$XGBOOST_ENRICHED_OUTPUT"

if [ $? -ne 0 ]; then
    echo "❌ Erreur lors de l'ajout des URLs d'images aux prédictions."
    exit 1
fi
echo "✅ URLs des images ajoutées avec succès. Fichier mis à jour : $XGBOOST_ENRICHED_OUTPUT"

# Vérifier que le fichier enrichi a bien été généré
if [ ! -f "$XGBOOST_ENRICHED_OUTPUT" ]; then
    echo "❌ Erreur : Fichier $XGBOOST_ENRICHED_OUTPUT introuvable après l'ajout des images."
    exit 1
fi


# Étape 3 : Exécuter le modèle de vision par ordinateur
echo "Lancement du modèle de vision par ordinateur..."
python3 /home/utilisateur/Documents/Certification/certification_global/E3_model_AI/model_ml/computer_vision.py \
    --input "$XGBOOST_ENRICHED_OUTPUT" \
    --output "$VISION_OUTPUT" \
    --model "$YOLO_MODEL" \
    --positive_output "${VISION_DIR}/positive_predictions.csv" \
    --error_log "${VISION_DIR}/error_images.csv"
if [ $? -ne 0 ]; then
    echo "Erreur lors de l'exécution du modèle de vision par ordinateur."
    exit 1
fi
echo "Modèle de vision par ordinateur terminé avec succès. Résultats dans $VISION_OUTPUT."

# Vérifier que le fichier de vision existe
if [ ! -f "$VISION_OUTPUT" ]; then
    echo "Erreur : Fichier $VISION_OUTPUT introuvable après le modèle de vision par ordinateur."
    exit 1
fi


# Pipeline terminé
echo "Pipeline global terminé avec succès."