# Documentation API REST

## 1. Vue d'ensemble
L'API REST fournit un accès sécurisé aux données des produits e-commerce.

## 2. Authentification
L'API utilise JWT (JSON Web Tokens) pour l'authentification :

```bash
POST /token
Content-Type: application/x-www-form-urlencoded
username=xxx&password=xxx
```

## 3. Points de terminaison

### Obtenir un token

```bash
POST /token
Content-Type: application/x-www-form-urlencoded
username=xxx&password=xxx
```

### Liste des produits

```bash
GET /products
Authorization: Bearer <token>
```

### Détails d'un produit

```bash
GET /products/product{id}
Authorization: Bearer <token>
```

### Images d'un produit

```bash
GET /products/{product_id}/images
Authorization: Bearer <token>
```

## Construction et démarrage 

```bash
docker compose up --build
```

L'API sera disponible à l'adresse : http://localhost:8000






