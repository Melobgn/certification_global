from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from datetime import datetime

class Product(BaseModel):
    product_id: int
    url: str
    title: str
    description: str

    model_config = ConfigDict(from_attributes=True)

class ProductWithPrediction(Product):
    is_weapon_pred: int

class User(BaseModel):
    username: str
    disabled: Optional[bool] = None

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None
