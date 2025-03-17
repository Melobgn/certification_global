# Documentation Base de Données

## 1. Modélisation des données

### Modèle Conceptuel des Données (MCD)

#### Entités et Relations

1. **SITE**
   - site_id (PK)
   - name (unique) 
   - url

2. **PRODUCT**
   - product_id (PK)
   - site_id (FK)
   - url
   - brand
   - title
   - description
   - model
   - generic_name

3. **PRODUCT_IMAGE**
   - image_id (PK)
   - product_id (FK)
   - image_url

4. **CLASSIFICATION_HISTORY**
   - classification_id (PK)
   - product_id (FK)
   - is_weapon
   - confidence_score
   - model_version
   - classification_date

#### Relations
- Un SITE peut avoir plusieurs PRODUCTS (1:N)
- Un PRODUCT peut avoir plusieurs PRODUCT_IMAGES (1:N) 
- Un PRODUCT peut avoir plusieurs CLASSIFICATION_HISTORY (1:N)

### Modèle Physique des Données (MPD)

Le schéma est implémenté dans `database/schema.sql` :

```sql
CREATE TABLE site (
    site_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    url TEXT NOT NULL
);

CREATE TABLE product (
    product_id INTEGER PRIMARY KEY AUTOINCREMENT,
    site_id INTEGER NOT NULL,
    url TEXT NOT NULL,
    brand TEXT,
    title TEXT,
    description TEXT,
    model TEXT,
    generic_name TEXT,
    FOREIGN KEY (site_id) REFERENCES site(site_id)
);
```

## 2. Choix Technologiques

### Base de données : SQLite3
SQLite a été choisi pour :
- Sa légèreté et portabilité (base de données fichier)
- Son intégration native avec Python
- Sa capacité à gérer notre volume de données
- Sa simplicité de sauvegarde et restauration

### Langage : Python
Python est utilisé pour :
- Les scripts d'import de données
- Les scripts de nettoyage RGPD
- L'API FastAPI


## 3. Optimisation de la base de données

### Optimisation des requêtes

#### Requêtes fréquentes

```sql
SELECT * FROM product WHERE title LIKE '%produit%';
```

#### Requêtes complexes

```sql
SELECT p.title, p.description, p.generic_name, s.url 
FROM product p 
JOIN site s ON p.site_id = s.site_id 
WHERE p.title LIKE '%produit%' 
AND p.description LIKE '%description%' 
AND p.generic_name LIKE '%nom_générique%';
```                                     


## 4. Gestion des données

### Nettoyage des données

#### Suppression des données obsolètes

```python
from database.cleanup import cleanup_old_data

cleanup_old_data()  
```

#### Optimisation de la base de données

```python
from database.cleanup import optimize_database

optimize_database()
```





