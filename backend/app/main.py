"""
FastAPI application main file.
Provides REST API for product catalog and conversational recommendations.
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from typing import List, Optional
import logging
from pathlib import Path
import sys
import os

# Add parent directory to path to allow imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.product import (
    Product,
    ProductFilter,
    ChatRecommendationRequest,
    ChatRecommendationResponse
)
from services import product_catalog
from services.nlp import parse_user_query_to_filters
from services.recommendation import recommend_products_from_query

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown.
    Loads product catalog on startup.
    """
    logger.info("Starting up...")
    
    # Load product catalog
    try:
        # Look for product JSON in data directory
        data_dir = Path(__file__).parent.parent.parent / "data"
        
        # Try to load watches data (or any available data)
        json_files = list(data_dir.glob("products_*.json"))
        
        if json_files:
            # Load the first available product file
            product_file = json_files[0]
            logger.info(f"Loading products from: {product_file}")
            count = product_catalog.load_products_from_json(str(product_file))
            logger.info(f"Loaded {count} products into catalog")
            
            # Log catalog stats
            stats = product_catalog.get_catalog().get_stats()
            logger.info(f"Catalog stats: {stats}")
        else:
            logger.warning(f"No product files found in {data_dir}")
            logger.warning("Catalog will be empty. Run the scraper first to populate data.")
    
    except Exception as e:
        logger.error(f"Failed to load product catalog: {e}")
        logger.warning("Continuing with empty catalog")
    
    yield
    
    logger.info("Shutting down...")


# Initialize FastAPI app
app = FastAPI(
    title="Virtual Try-On Product Recommendation API",
    description="REST API for product search and conversational recommendations",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS (allow frontend to access API)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# ENDPOINTS
# ============================================================================

@app.get("/health", tags=["System"])
async def health_check():
    """
    Health check endpoint.
    Returns API status and catalog information.
    """
    catalog = product_catalog.get_catalog()
    stats = catalog.get_stats() if catalog.is_loaded() else None
    
    return {
        "status": "ok",
        "message": "API is running",
        "catalog_loaded": catalog.is_loaded(),
        "total_products": stats['total_products'] if stats else 0,
        "version": "1.0.0"
    }


@app.get("/products", response_model=List[Product], tags=["Products"])
async def list_products(
    # Price filters
    min_price: Optional[float] = Query(None, description="Minimum price"),
    max_price: Optional[float] = Query(None, description="Maximum price"),
    
    # Category filters
    category: Optional[str] = Query(None, description="Product category"),
    sub_category: Optional[str] = Query(None, description="Product subcategory"),
    brand: Optional[str] = Query(None, description="Brand name"),
    
    # Attribute filters (examples for watches)
    gender: Optional[str] = Query(None, description="Gender (Men/Women/Unisex)"),
    style: Optional[str] = Query(None, description="Style (Formal/Casual/Sport)"),
    
    # Text search
    search: Optional[str] = Query(None, description="Search query"),
    
    # Pagination
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    limit: int = Query(50, ge=1, le=200, description="Max results to return"),
):
    """
    List products with optional filters.
    
    **Examples:**
    - `/products?max_price=10000&gender=men&style=formal`
    - `/products?search=wedding elegant&min_price=5000`
    - `/products?brand=Titan&limit=20`
    """
    try:
        # Build attribute filters
        attributes = {}
        if gender:
            attributes['gender'] = gender
        if style:
            attributes['style'] = style
        
        # Create filter object
        filters = ProductFilter(
            min_price=min_price,
            max_price=max_price,
            category=category,
            sub_category=sub_category,
            brand=brand,
            attributes=attributes,
            search_query=search,
            offset=offset,
            limit=limit
        )
        
        # Get filtered products
        products = product_catalog.filter_products(filters)
        
        return products
    
    except Exception as e:
        logger.error(f"Error listing products: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/products/{product_id}", response_model=Product, tags=["Products"])
async def get_product(product_id: str):
    """
    Get a single product by ID.
    
    **Example:**
    - `/products/titan-watch-123`
    """
    try:
        product = product_catalog.get_product_by_id(product_id)
        
        if product is None:
            raise HTTPException(
                status_code=404,
                detail=f"Product not found: {product_id}"
            )
        
        return product
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting product {product_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/catalog/stats", tags=["Catalog"])
async def get_catalog_stats():
    """
    Get catalog statistics.
    
    Returns information about available products, categories, brands, price ranges, etc.
    """
    try:
        catalog = product_catalog.get_catalog()
        
        if not catalog.is_loaded():
            return {
                "loaded": False,
                "message": "Catalog not loaded. Run scraper to populate data."
            }
        
        stats = catalog.get_stats()
        stats['loaded'] = True
        
        return stats
    
    except Exception as e:
        logger.error(f"Error getting catalog stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/chat/recommend", response_model=ChatRecommendationResponse, tags=["Recommendations"])
async def chat_recommend(request: ChatRecommendationRequest):
    """
    Get product recommendations from natural language query.
    
    **Example:**
    ```json
    {
        "user_query": "I need a formal men's watch for a wedding under 10000 rupees"
    }
    ```
    
    Returns:
    - Parsed understanding of the query
    - Recommended products
    - Natural language explanation
    """
    try:
        logger.info(f"Chat recommendation request: {request.user_query}")
        
        # Parse user query to structured filters
        query_understanding = parse_user_query_to_filters(request.user_query)
        
        logger.info(f"Query understanding: {query_understanding}")
        
        # Get product recommendations
        response = recommend_products_from_query(
            query_understanding=query_understanding,
            user_query=request.user_query
        )
        
        return response
    
    except Exception as e:
        logger.error(f"Error in chat recommendation: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Recommendation failed: {str(e)}"
        )


# ============================================================================
# Run with: uvicorn backend.app.main:app --reload
# API docs at: http://localhost:8000/docs
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
