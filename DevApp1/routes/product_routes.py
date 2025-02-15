# routes/product_routes.py
from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel, Field
from typing import Optional
import sqlite3

import os


router = APIRouter()
DB_FILE = os.getenv("DB_FILE", "db/appFeb12.db")

# Database initialization
def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS products (
        product_id INTEGER PRIMARY KEY AUTOINCREMENT,
        product_name TEXT NOT NULL UNIQUE,
        status TEXT DEFAULT 'active' CHECK (status IN ('active', 'inactive')),
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
    );
    ''')
    
    conn.commit()
    conn.close()

# Initialize database on module import
init_db()

# Pydantic model for input validation
class ProductCreate(BaseModel):
    product_name: str = Field(..., min_length=1, description="Name of the product")

class ProductUpdate(BaseModel):
    product_name: Optional[str] = None
    status: Optional[str] = Field(None, pattern='^(active|inactive)$')


# API Routes
##############################################
@router.get("/products")
def get_products():
    print("line 48. products_routes.py")
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM products")
    
    products = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return products

# Create a new product #####################
@router.post("/products")
def create_product(product: ProductCreate):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO products (product_name) VALUES (?)", 
        (product.product_name,)
    )
    conn.commit()
    product_id = cursor.lastrowid
    conn.close()
    return {
        "product_id": product_id, 
        "message": "Product created successfully"
    }

# Update a product #####################
@router.put("/products/{product_id}")
def update_product(product_id: int, product: ProductUpdate):
    print(f"Updating product {product_id} with data:", product.dict())
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    # First check if product exists
    cursor.execute("SELECT product_id FROM products WHERE product_id = ?", (product_id,))
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="Product not found")

    try:
        # Prepare update query dynamically
        update_fields = []
        params = []

        if product.product_name is not None:
            update_fields.append("product_name = ?")
            params.append(product.product_name)

        if product.status is not None:
            update_fields.append("status = ?")
            params.append(product.status)

        if not update_fields:  # If no fields to update
            conn.close()
            return {"message": "No fields to update"}
        
        # Remove the updated_at field update since it's causing issues
        query = f"UPDATE products SET {', '.join(update_fields)} WHERE product_id = ?"
        params.append(product_id)

        cursor.execute(query, params)
        
        if cursor.rowcount == 0:
            conn.rollback()
            conn.close()
            raise HTTPException(status_code=400, detail="Update failed")
            
        conn.commit()
        conn.close()
        return {"message": "Product updated successfully"}
        
    except sqlite3.IntegrityError as e:
        conn.rollback()
        conn.close()
        raise HTTPException(status_code=400, detail="Product name already exists")
    except Exception as e:
        conn.rollback()
        conn.close()
        raise HTTPException(status_code=500, detail=str(e))




# DELETE a product #####################
@router.delete("/products/{product_id}")
def delete_product(product_id: int):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM products WHERE product_id = ?", (product_id,))
    conn.commit()
    conn.close()
    return {"message": "Product deleted"}

