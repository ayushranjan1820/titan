"""
Recommendation service with RAG-like flow.
Combines filtering, scoring, and LLM-based explanation.
"""

import logging
from typing import List, Dict, Any
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.product import Product, ProductFilter, ChatRecommendationResponse
from services import product_catalog
from services.nlp import generate_recommendation_explanation

logger = logging.getLogger(__name__)


def recommend_products_from_query(
    query_understanding: Dict[str, Any],
    user_query: str,
    top_k: int = 10
) -> ChatRecommendationResponse:
    """
    Main recommendation function that combines filtering and ranking.
    
    This implements a simplified RAG-like flow:
    1. Extract structured filters from query understanding
    2. Apply hard filters (price, gender, category)
    3. Apply soft scoring (occasion, style, preferences)
    4. Rank and return top-K products
    5. Generate LLM explanation
    
    Args:
        query_understanding: Parsed user query with extracted filters
        user_query: Original user query string
        top_k: Number of products to return
        
    Returns:
        ChatRecommendationResponse with products and explanation
    """
    try:
        logger.info("Generating product recommendations")
        
        # Step 1: Convert query understanding to ProductFilter
        product_filter = _build_product_filter(query_understanding)
        
        # Step 2: Get all matching products (with hard filters applied)
        # Use max limit of 200 to avoid validation errors
        matching_products = product_catalog.filter_products(
            min_price=product_filter.min_price,
            max_price=product_filter.max_price,
            category=product_filter.category,
            brand=product_filter.brand,
            attributes=product_filter.attributes,
            search_query=product_filter.search_query,
            offset=0,
            limit=200  # Max allowed by ProductFilter validation
        )
        
        total_matches = len(matching_products)
        logger.info(f"Found {total_matches} products after hard filtering")
        
        # Step 3: Apply soft scoring and ranking
        if matching_products:
            scored_products = _score_products(
                products=matching_products,
                preferences=query_understanding
            )
            
            # Take top-K
            top_products = scored_products[:top_k]
        else:
            top_products = []
        
        logger.info(f"Returning top {len(top_products)} products")
        
        # Step 4: Generate natural language explanation
        explanation = generate_recommendation_explanation(
            user_query=user_query,
            filters=query_understanding,
            products=top_products,
            num_total=total_matches
        )
        
        # Step 5: Build response
        response = ChatRecommendationResponse(
            query_understanding=query_understanding,
            products=top_products,
            llm_explanation=explanation,
            total_matches=total_matches
        )
        
        return response
    
    except Exception as e:
        logger.error(f"Error in recommendation: {e}", exc_info=True)
        raise


def _build_product_filter(query_understanding: Dict[str, Any]) -> ProductFilter:
    """
    Convert query understanding to ProductFilter.
    
    Args:
        query_understanding: Extracted filters from NLP
        
    Returns:
        ProductFilter object
    """
    # Build attributes dict from gender, style, color
    attributes = {}
    
    if query_understanding.get("gender"):
        attributes["gender"] = query_understanding["gender"]
    
    if query_understanding.get("style"):
        attributes["style"] = query_understanding["style"]
    
    if query_understanding.get("color"):
        attributes["color"] = query_understanding["color"]
    
    # Build search query from additional preferences
    # NOTE: We don't include occasion or additional_preferences in hard search
    # because they're too restrictive (require ALL terms to match).
    # Instead, we use them for soft scoring/ranking.
    search_terms = []
    
    # Only use explicit search_query if provided
    if query_understanding.get("search_query"):
        search_query = query_understanding["search_query"]
    else:
        search_query = None
    
    return ProductFilter(
        min_price=query_understanding.get("min_price"),
        max_price=query_understanding.get("max_price"),
        category=query_understanding.get("category"),
        brand=query_understanding.get("brand"),
        attributes=attributes,
        search_query=search_query,
        # Use occasion and preferences for scoring, not hard filtering
        preferred_features=query_understanding.get("additional_preferences", [])
    )


def _score_products(
    products: List[Product],
    preferences: Dict[str, Any]
) -> List[Product]:
    """
    Score and rank products based on soft preferences.
    
    Scoring factors:
    - Occasion match
    - Style match
    - Preferred features
    - Brand preference
    - Description/name relevance
    
    Args:
        products: List of products to score
        preferences: User preferences from query understanding
        
    Returns:
        Sorted list of products (highest score first)
    """
    scored_products = []
    
    occasion = preferences.get("occasion", "").lower()
    style = preferences.get("style", "").lower()
    additional_prefs = [p.lower() for p in preferences.get("additional_preferences", [])]
    
    for product in products:
        score = 0.0
        
        # Base score (everyone starts equal)
        score += 1.0
        
        # Occasion boost
        if occasion:
            # Check in name, description, features
            searchable = (
                (product.name or "").lower() +
                (product.description or "").lower() +
                " ".join(product.features).lower()
            )
            
            if occasion in searchable:
                score += 5.0
            elif any(word in searchable for word in occasion.split()):
                score += 2.0
        
        # Style boost (partially covered by hard filter, but boost exact matches)
        if style:
            product_style = product.attributes.get("style", "").lower()
            if style == product_style:
                score += 3.0
            elif style in product_style or product_style in style:
                score += 1.5
        
        # Additional preferences boost
        for pref in additional_prefs:
            product_text = (
                (product.name or "").lower() +
                (product.description or "").lower() +
                " ".join(product.features).lower() +
                " ".join(str(v) for v in product.attributes.values()).lower()
            )
            
            if pref in product_text:
                score += 2.0
        
        # Feature count boost (more features = more value)
        score += len(product.features) * 0.1
        
        # Price preference (prefer products closer to budget if max_price is set)
        max_price = preferences.get("max_price")
        if max_price and product.price:
            # Products closer to the max (but under) score higher
            # Assuming people want best value near their budget
            price_ratio = product.price / max_price
            if price_ratio >= 0.7 and price_ratio <= 1.0:
                score += 2.0  # Sweet spot
            elif price_ratio < 0.7:
                score += 1.0  # More affordable
        
        scored_products.append((score, product))
    
    # Sort by score (descending)
    scored_products.sort(key=lambda x: x[0], reverse=True)
    
    # Log top scores for debugging
    if scored_products:
        logger.debug(f"Top 3 scores: {[(s, p.name) for s, p in scored_products[:3]]}")
    
    return [product for _, product in scored_products]


# ============================================================================
# RAG FLOW (STUB FOR FUTURE ENHANCEMENT)
# ============================================================================

def create_product_embeddings(products: List[Product]) -> Any:
    """
    Create embeddings for products (stub for future implementation).
    
    In a full RAG implementation, this would:
    1. Convert each product to a text description
    2. Generate embeddings using an embedding model
    3. Store in a vector database
    
    Args:
        products: List of products
        
    Returns:
        Embedding store or index
    """
    # TODO: Implement with actual embedding model
    # Example with sentence-transformers:
    # from sentence_transformers import SentenceTransformer
    # model = SentenceTransformer('all-MiniLM-L6-v2')
    # texts = [_product_to_text(p) for p in products]
    # embeddings = model.encode(texts)
    # return embeddings
    
    logger.warning("Embedding creation not implemented - using keyword-based search")
    return None


def semantic_search(query: str, embedding_store: Any, top_k: int = 20) -> List[int]:
    """
    Perform semantic search on products (stub for future implementation).
    
    Args:
        query: User query
        embedding_store: Embedding index/database
        top_k: Number of results
        
    Returns:
        List of product indices
    """
    # TODO: Implement with vector search
    # Example with faiss:
    # query_embedding = embedding_model.encode([query])
    # distances, indices = index.search(query_embedding, top_k)
    # return indices[0].tolist()
    
    logger.warning("Semantic search not implemented - using filtering")
    return []


def _product_to_text(product: Product) -> str:
    """
    Convert product to text for embedding.
    
    Args:
        product: Product object
        
    Returns:
        Text representation
    """
    parts = [
        f"Product: {product.name}",
        f"Brand: {product.brand}" if product.brand else "",
        f"Category: {product.category}",
        f"Price: ₹{product.price}" if product.price else "",
        f"Description: {product.description}" if product.description else "",
        f"Features: {', '.join(product.features)}" if product.features else "",
        f"Attributes: {', '.join(f'{k}: {v}' for k, v in product.attributes.items())}"
    ]
    
    return " | ".join(p for p in parts if p)
