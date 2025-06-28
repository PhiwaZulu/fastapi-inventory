from pydantic import BaseModel
from typing import Optional

# Inventory model for input (request bodies)
class InventoryItem(BaseModel):
    name: str
    quantity: int
    price: float
    description: Optional[str] = None

    class Config:
        schema_extra = {
            "example": {
                "name": "Laptop",
                "quantity": 10,
                "price": 999.99,
                "description": "High performance laptop"
            }
        }

# Inventory model for responses (includes metadata)
class InventoryItemResponse(InventoryItem):
    created_by: str

    class Config:
        schema_extra = {
            "example": {
                "name": "Smartphone",
                "quantity": 20,
                "price": 499.99,
                "description": "Latest model smartphone",
                "created_by": "admin_user"
            }
        }

# Public User model (used in route responses and token dependency)
class User(BaseModel):
    username: str
    full_name: Optional[str] = None
    role: str
    disabled: Optional[bool] = False

# Internal User model with hashed password (used in fake DB)
class UserInDB(User):
    hashed_password: str

# Registration request model
class RegisterRequest(BaseModel):
    username: str
    password: str  # Plain-text password submitted by user
    full_name: Optional[str] = None
    role: str = "user"  # Default role

    class Config:
        schema_extra = {
            "example": {
                "username": "john_doe",
                "password": "strong_password123",
                "full_name": "John Doe",
                "role": "user"
            }
        }
