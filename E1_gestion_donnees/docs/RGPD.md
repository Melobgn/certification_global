# Documentation RGPD

## 1. Nature des données collectées

### Données produits
- Titre du produit
- Description
- Prix
- URLs des images
- Marque et modèle
- Catégorie générique
- URL du produit

### Données techniques
- Logs de traitement
- Dates de collecte
- Statuts des opérations

## 2. Finalités du traitement

- Analyse des produits e-commerce
- Détection et classification des articles
- Statistiques sur les produits

## 3. Base légale

- Intérêt légitime (Article 6.1.f du RGPD)
- Données publiquement accessibles
- Pas de collecte de données personnelles

## 4. Durée de conservation

### Données produits
- Conservation : 12 mois
- Suppression automatique via cleanup.py
- Vérification mensuelle

### Logs techniques
- Conservation : 6 mois
- Nettoyage automatique
- Archivage des erreurs importantes

## 5. Mesures techniques

### Sécurité
- Base de données locale SQLite
- Logs d'accès et de modifications
- Sauvegarde régulière

### Nettoyage automatique
- Script : database/cleanup.py
- Fréquence : Mensuelle
- Actions :
  - Suppression des données anciennes
  - Nettoyage des images orphelines
  - Optimisation de la base

## 6. Procédures de maintenance

### Automatiques
- Nettoyage mensuel des données
- Vérification des liens morts
- Optimisation de la base

### Manuelles
- Vérification trimestrielle des données
- Contrôle des logs d'erreurs
- Mise à jour de la documentation

## 7. Responsabilités

### Administrateur système
- Surveillance des processus automatiques
- Vérification des logs
- Maintenance de la base

### Développeur
- Mise à jour des scripts
- Correction des bugs
- Amélioration des processus

## 8. Mise à jour

Cette documentation est revue :
- Tous les 6 mois
- Lors des modifications majeures
- En cas d'évolution réglementaire