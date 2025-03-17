from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class Product(BaseModel):
    product_id: int
    site_id: int
    url: str
    title: str
    description: Optional[str] = None
    brand: Optional[str] = None
    model: Optional[str] = None
    generique: Optional[str] = None  # Correspond à generic_name dans la BDD
    created_at: Optional[datetime] = None  # Rend le champ optionnel

    
    # Configuration pour Pydantic
    class Config:
        from_attributes = True

class ProductWithImages(Product):
    images: List[str] = []  # Pour joindre les URLs des images depuis product_image

class User(BaseModel):
    username: str
    disabled: Optional[bool] = None

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None 