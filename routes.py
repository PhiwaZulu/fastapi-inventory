import random
import time
from fastapi import APIRouter, Depends, HTTPException, status, Query, Response, Body
from typing import Dict, Optional
from fastapi.security import OAuth2PasswordRequestForm
from models import InventoryItem, RegisterRequest, UserInDB, User, InventoryItemResponse
from auth import (
    authenticate_user, create_access_token, fake_users_db,
    get_password_hash, get_current_active_user, get_admin_user
)

router = APIRouter()

# In-memory inventory and auto-incrementing ID tracker
inventory: Dict[int, dict] = {}
next_item_id = 1

# Register new user
@router.post("/register", status_code=201, tags=["Authentication"], summary="Register a new user",
             response_model=dict)
def register_user(
    user: RegisterRequest = Body(
        ...,
        example={
            "username": "new_user",
            "password": "strong_password123",
            "full_name": "New User",
            "role": "user"
        }
    )
):
    if user.username in fake_users_db:
        raise HTTPException(status_code=400, detail="User already exists")

    hashed_pw = get_password_hash(user.password)
    fake_users_db[user.username] = UserInDB(
        username=user.username,
        full_name=user.full_name,
        role=user.role,
        hashed_password=hashed_pw
    )
    return {"msg": f"User '{user.username}' registered successfully."}

# Login to obtain JWT token
@router.post("/token", tags=["Authentication"], summary="Login and get access token")
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    access_token = create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}

# Public welcome message
@router.get("/", tags=["General"], summary="Welcome message")
def root():
    return {"message": "Welcome to the Inventory Management API!"}

# List items with optional filters, pagination, and sorting (user or admin)
@router.get("/items/", tags=["Inventory"], summary="List inventory items with filters, pagination, and sorting")
def list_items(
    name: Optional[str] = Query(None, description="Filter by item name"),
    min_price: Optional[float] = Query(None, ge=0, description="Minimum price"),
    max_price: Optional[float] = Query(None, ge=0, description="Maximum price"),
    min_quantity: Optional[int] = Query(None, ge=0, description="Minimum quantity"),
    skip: int = Query(0, ge=0, description="Number of items to skip"),
    limit: int = Query(10, ge=1, le=50, description="Maximum number of items to return"),
    sort_by: str = Query("name", regex="^(name|price|quantity)$", description="Sort by 'name', 'price' or 'quantity'"),
    order: str = Query("asc", regex="^(asc|desc)$", description="Sort order: 'asc' or 'desc'"),
    current_user: User = Depends(get_current_active_user)
):
    results = []
    for item_id, item in inventory.items():
        if name and name.lower() not in item["name"].lower():
            continue
        if min_price is not None and item["price"] < min_price:
            continue
        if max_price is not None and item["price"] > max_price:
            continue
        if min_quantity is not None and item["quantity"] < min_quantity:
            continue
        results.append({"item_id": item_id, **item})
    
    # Sorting
    reverse = order == "desc"
    results.sort(key=lambda x: x[sort_by], reverse=reverse)

    # Pagination
    paginated = results[skip : skip + limit]

    return {
        "total": len(results),
        "skip": skip,
        "limit": limit,
        "items": paginated
    }

# Get specific item by ID (requires authentication)
@router.get("/items/{item_id}", tags=["Inventory"], summary="Get specific inventory item by ID",
            response_model=InventoryItemResponse)
def get_item(item_id: int, current_user: User = Depends(get_current_active_user)):
    if item_id not in inventory:
        raise HTTPException(status_code=404, detail="Item not found")
    return {"item_id": item_id, **inventory[item_id]}

# Add a new item (admin only, item_id auto-generated + logs creator)
@router.post("/items/", status_code=201, tags=["Inventory"], summary="Add a new inventory item (admin only)",
             response_model=InventoryItemResponse)
def add_item(
    item: InventoryItem = Body(
        ...,
        example={
            "name": "Laptop",
            "quantity": 10,
            "price": 999.99,
            "description": "High performance laptop"
        }
    ),
    current_user: User = Depends(get_admin_user)
):
    global next_item_id
    item_id = next_item_id
    inventory[item_id] = {
        **item.dict(),
        "created_by": current_user.username
    }
    next_item_id += 1
    return {"item_id": item_id, **inventory[item_id]}

# Update existing item (admin only)
@router.put("/items/{item_id}", tags=["Inventory"], summary="Update an existing inventory item (admin only)",
            response_model=InventoryItemResponse)
def update_item(item_id: int, item: InventoryItem, current_user: User = Depends(get_admin_user)):
    if item_id not in inventory:
        raise HTTPException(status_code=404, detail="Item not found")
    existing = inventory[item_id]
    inventory[item_id] = {
        **item.dict(),
        "created_by": existing.get("created_by", current_user.username)
    }
    return {"item_id": item_id, **inventory[item_id]}

# Delete item (admin only)
@router.delete("/items/{item_id}", status_code=204, tags=["Inventory"], summary="Delete an inventory item (admin only)")
def delete_item(item_id: int, current_user: User = Depends(get_admin_user)):
    if item_id not in inventory:
        raise HTTPException(status_code=404, detail="Item not found")
    del inventory[item_id]
    return Response(status_code=204)

# Simulate random server errors for testing
@router.get("/simulate-error", tags=["Testing"], summary="Simulate random server errors for testing")
def simulate_error(
    error_rate: float = Query(0.3, ge=0, le=1, description="Probability of returning an error (0 to 1)"),
    current_user: User = Depends(get_current_active_user)
):
    """
    Simulates server errors randomly based on the given error_rate.
    Example: error_rate=0.3 means 30% chance to return a 500 error.
    """
    if random.random() < error_rate:
        # Randomly pick an error code to simulate
        error_code = random.choice([500, 502, 503])
        raise HTTPException(status_code=error_code, detail=f"Simulated error {error_code}")
    return {"message": "Success - no error simulated"}

# Simulate slow responses with delay
@router.get("/simulate-delay", tags=["Testing"], summary="Simulate slow responses with delay")
def simulate_delay(
    delay_seconds: int = Query(5, ge=1, le=30, description="Seconds to delay the response"),
    current_user: User = Depends(get_current_active_user)
):
    """
    Simulates a slow server response by delaying the API response.
    Useful for testing timeout handling.
    """
    time.sleep(delay_seconds)
    return {"message": f"Response delayed by {delay_seconds} seconds"}
