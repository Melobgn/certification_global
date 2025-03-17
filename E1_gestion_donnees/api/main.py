from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from datetime import datetime, timedelta
import sqlite3
from typing import List
from .models import Product, User, Token, ProductWithImages
from .database import get_db
import os
from dotenv import load_dotenv
from pathlib import Path

# Charger le .env depuis le dossier api/
env_path = Path(__file__).parent / '.env'
load_dotenv(env_path)

app = FastAPI(
    title="API Détection d'Armes",
    description="API REST pour accéder aux données des produits e-commerce",
    version="1.0.0"
)

# Configuration sécurité
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))

# Configuration authentification
API_USERNAME = os.getenv("API_USERNAME")
API_PASSWORD = os.getenv("API_PASSWORD")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Routes API
@app.post("/token", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Identifiants incorrects",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(
        data={"sub": user.username}
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/products/", response_model=List[ProductWithImages])
async def read_products(skip: int = 0, limit: int = 100, token: str = Depends(oauth2_scheme)):
    with get_db() as db:
        cursor = db.cursor()
        cursor.execute("""
            SELECT 
                p.*,
                GROUP_CONCAT(pi.image_url) as images
            FROM product p
            LEFT JOIN product_image pi ON p.product_id = pi.product_id
            GROUP BY p.product_id
            LIMIT ? OFFSET ?
        """, (limit, skip))
        
        products = []
        for row in cursor.fetchall():
            product_dict = dict(row)
            # Convertir la chaîne d'images en liste
            if product_dict.get('images'):
                product_dict['images'] = product_dict['images'].split(',')
            else:
                product_dict['images'] = []
            products.append(product_dict)
        
        return products

@app.get("/products/{product_id}", response_model=ProductWithImages)
async def read_product(product_id: int, token: str = Depends(oauth2_scheme)):
    with get_db() as db:
        cursor = db.cursor()
        cursor.execute("""
            SELECT 
                p.*,
                GROUP_CONCAT(pi.image_url) as images
            FROM product p
            LEFT JOIN product_image pi ON p.product_id = pi.product_id
            WHERE p.product_id = ?
            GROUP BY p.product_id
        """, (product_id,))
        
        row = cursor.fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail="Produit non trouvé")
            
        product_dict = dict(row)
        if product_dict.get('images'):
            product_dict['images'] = product_dict['images'].split(',')
        else:
            product_dict['images'] = []
            
        return product_dict 

@app.get("/products/{product_id}/images", response_model=List[str])
async def get_product_images(product_id: int, token: str = Depends(oauth2_scheme)):
    """Récupère uniquement les URLs des images d'un produit pour l'analyse CV"""
    with get_db() as db:
        cursor = db.cursor()
        cursor.execute("""
            SELECT image_url
            FROM product_image
            WHERE product_id = ?
        """, (product_id,))
        
        images = [row['image_url'] for row in cursor.fetchall()]
        if not images:
            raise HTTPException(status_code=404, detail="Aucune image trouvée")
            
        return images 

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def authenticate_user(username: str, password: str):
    if username == API_USERNAME and password == API_PASSWORD:
        return User(username=username)
    return None 