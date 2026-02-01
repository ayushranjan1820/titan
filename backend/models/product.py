"""
Product data models using Pydantic.
Defines the schema for products across different categories.
"""

from pydantic import BaseModel, Field, HttpUrl
from typing import Optional, List, Dict, Any
from datetime import datetime


class Product(BaseModel):
    """
    Universal product model.
    Designed to be flexible across different product categories.
    """
    
    # Core identification
    id: str = Field(..., description="Unique product identifier")
    product_url: str = Field(..., description="URL to product page")
    
    # Basic information
    name: str = Field(..., description="Product name/title")
    description: Optional[str] = Field(None, description="Product description")
    
    # Pricing
    price: Optional[float] = Field(None, description="Product price (numeric)")
    currency: str = Field(default="INR", description="Currency code")
    
    # Classification
    category: str = Field(..., description="Main category (e.g., watches, grocery, apparel)")
    sub_category: Optional[str] = Field(None, description="Subcategory")
    brand: Optional[str] = Field(None, description="Brand name")
    
    # Category-specific attributes (flexible key-value storage)
    attributes: Dict[str, Any] = Field(
        default_factory=dict,
        description="Category-specific attributes (gender, style, material, etc.)"
    )
    
    # Features and specifications
    features: List[str] = Field(
        default_factory=list,
        description="List of product features"
    )
    
    # Media
    image_url: Optional[str] = Field(None, description="Primary product image URL")
    image_urls_all: List[str] = Field(
        default_factory=list,
        description="All product images"
    )
    
    # Metadata
    scraped_at: Optional[datetime] = Field(
        default_factory=datetime.now,
        description="Timestamp when product was scraped"
    )
    
    class Config:
        """Pydantic config."""
        json_schema_extra = {
            "example": {
                "id": "titan-watch-123",
                "product_url": "https://example.com/products/titan-watch-123",
                "name": "Titan Raga Elegance",
                "description": "Elegant formal watch with leather strap",
                "price": 8999.0,
                "currency": "INR",
                "category": "watches",
                "sub_category": "mens-watches",
                "brand": "Titan",
                "attributes": {
                    "gender": "Men",
                    "style": "Formal",
                    "material": "Leather strap, Stainless steel case",
                    "dial_color": "Silver",
                    "movement": "Quartz",
                    "water_resistance": "30m"
                },
                "features": [
                    "Water resistant",
                    "Scratch resistant glass",
                    "Date display"
                ],
                "image_url": "https://example.com/images/titan-watch-123.jpg",
                "image_urls_all": [
                    "https://example.com/images/titan-watch-123-1.jpg",
                    "https://example.com/images/titan-watch-123-2.jpg"
                ]
            }
        }


class ProductFilter(BaseModel):
    """
    Filter criteria for product search.
    Supports both hard filters (exact match) and soft filters (scoring).
    """
    
    # Price range
    min_price: Optional[float] = None
    max_price: Optional[float] = None
    
    # Category
    category: Optional[str] = None
    sub_category: Optional[str] = None
    brand: Optional[str] = None
    
    # Attribute filters (flexible)
    # Example: {"gender": "Men", "style": "Formal"}
    attributes: Dict[str, str] = Field(default_factory=dict)
    
    # Text search
    search_query: Optional[str] = None
    
    # Soft filters for scoring/ranking
    preferred_features: List[str] = Field(
        default_factory=list,
        description="Features to boost in ranking"
    )
    
    # Pagination
    offset: int = Field(default=0, ge=0)
    limit: int = Field(default=50, ge=1, le=200)
    
    class Config:
        """Pydantic config."""
        json_schema_extra = {
            "example": {
                "min_price": 5000,
                "max_price": 15000,
                "category": "watches",
                "attributes": {
                    "gender": "Men",
                    "style": "Formal"
                },
                "search_query": "wedding formal elegant",
                "limit": 20
            }
        }


class ChatRecommendationRequest(BaseModel):
    """Request model for conversational recommendations."""
    
    user_query: str = Field(
        ...,
        description="Natural language query from user",
        min_length=3
    )
    
    # Optional context
    user_preferences: Optional[Dict[str, Any]] = Field(
        None,
        description="Known user preferences"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "user_query": "I need a formal men's watch for a wedding under 10000 rupees"
            }
        }


class ChatRecommendationResponse(BaseModel):
    """Response model for conversational recommendations."""
    
    # Parsed understanding
    query_understanding: Dict[str, Any] = Field(
        ...,
        description="Structured interpretation of user query"
    )
    
    # Recommended products
    products: List[Product] = Field(
        ...,
        description="Recommended products matching query"
    )
    
    # LLM explanation
    llm_explanation: str = Field(
        ...,
        description="Natural language explanation of recommendations"
    )
    
    # Metadata
    total_matches: int = Field(
        ...,
        description="Total number of products matching filters"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "query_understanding": {
                    "occasion": "wedding",
                    "gender": "men",
                    "style": "formal",
                    "max_price": 10000,
                    "preferences": ["elegant", "classic"]
                },
                "products": [],  # List of Product objects
                "llm_explanation": "Based on your requirements for a formal men's watch for a wedding under ₹10,000, I've selected these elegant timepieces that would be perfect for the occasion.",
                "total_matches": 15
            }
        }
