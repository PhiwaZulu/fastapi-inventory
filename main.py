from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Optional

# Create FastAPI app instance
app = FastAPI(title="Inventory Management API")

# Define data model for inventory item
class InventoryItem(BaseModel):
    name: str
    quantity: int
    price: float
    description: Optional[str] = None  # Optional field

# In-memory storage for items: key is item_id, value is InventoryItem
inventory: Dict[int, InventoryItem] = {}

# Root endpoint
@app.get("/")
def read_root():
    return {"message": "Welcome to the Inventory Management API!"}

# Add a new inventory item
@app.post("/items/", status_code=201)
def add_item(item_id: int, item: InventoryItem):
    if item_id in inventory:
        raise HTTPException(status_code=400, detail="Item ID already exists")
    inventory[item_id] = item
    return {"item_id": item_id, **item.dict()}

# Get an inventory item by ID
@app.get("/items/{item_id}")
def get_item(item_id: int):
    if item_id not in inventory:
        raise HTTPException(status_code=404, detail="Item not found")
    return {"item_id": item_id, **inventory[item_id].dict()}

# Update an existing inventory item
@app.put("/items/{item_id}")
def update_item(item_id: int, item: InventoryItem):
    if item_id not in inventory:
        raise HTTPException(status_code=404, detail="Item not found")
    inventory[item_id] = item
    return {"item_id": item_id, **item.dict()}

# Delete an inventory item
@app.delete("/items/{item_id}", status_code=204)
def delete_item(item_id: int):
    if item_id not in inventory:
        raise HTTPException(status_code=404, detail="Item not found")
    del inventory[item_id]
    return {}

# List all inventory items
@app.get("/items/")
def list_items():
    return [{"item_id": id, **item.dict()} for id, item in inventory.items()]
