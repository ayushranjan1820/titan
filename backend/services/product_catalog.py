"""
Product catalog service.
Manages loading, storing, filtering, and searching products.
"""

import json
from typing import List, Dict, Any, Optional
from pathlib import Path
import logging
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.product import Product, ProductFilter

logger = logging.getLogger(__name__)


class ProductCatalog:
    """
    In-memory product catalog with filtering and search capabilities.
    Designed for POC - can be extended to use a database.
    """
    
    def __init__(self):
        """Initialize empty catalog."""
        self.products: List[Product] = []
        self._products_by_id: Dict[str, Product] = {}
        self._loaded = False
    
    def load_products_from_json(self, path: str) -> int:
        """
        Load products from a JSON file.
        
        Args:
            path: Path to JSON file containing products
            
        Returns:
            Number of products loaded
        """
        try:
            logger.info(f"Loading products from: {path}")
            
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Handle both direct array and wrapped format
            if isinstance(data, dict) and 'products' in data:
                products_data = data['products']
            elif isinstance(data, list):
                products_data = data
            else:
                raise ValueError("Invalid JSON format: expected array or object with 'products' key")
            
            # Parse products
            self.products = []
            self._products_by_id = {}
            
            for product_data in products_data:
                try:
                    product = Product(**product_data)
                    self.products.append(product)
                    self._products_by_id[product.id] = product
                except Exception as e:
                    logger.warning(f"Failed to parse product {product_data.get('id', 'unknown')}: {e}")
            
            self._loaded = True
            logger.info(f"Loaded {len(self.products)} products")
            
            return len(self.products)
            
        except FileNotFoundError:
            logger.error(f"Product file not found: {path}")
            raise
        except Exception as e:
            logger.error(f"Error loading products: {e}")
            raise
    
    def get_product_by_id(self, product_id: str) -> Optional[Product]:
        """
        Get a single product by ID.
        
        Args:
            product_id: Product identifier
            
        Returns:
            Product or None if not found
        """
        return self._products_by_id.get(product_id)
    
    def filter_products(
        self,
        filters: Optional[ProductFilter] = None,
        **kwargs
    ) -> List[Product]:
        """
        Filter products based on criteria.
        
        Args:
            filters: ProductFilter object with criteria
            **kwargs: Individual filter parameters (alternative to filters object)
            
        Returns:
            List of matching products
        """
        if filters is None:
            # Build filter from kwargs
            filters = ProductFilter(**kwargs)
        
        results = self.products.copy()
        
        # Apply hard filters
        
        # Price range
        if filters.min_price is not None:
            results = [p for p in results if p.price is not None and p.price >= filters.min_price]
        
        if filters.max_price is not None:
            results = [p for p in results if p.price is not None and p.price <= filters.max_price]
        
        # Category filters
        if filters.category:
            results = [p for p in results if p.category.lower() == filters.category.lower()]
        
        if filters.sub_category:
            results = [
                p for p in results
                if p.sub_category and p.sub_category.lower() == filters.sub_category.lower()
            ]
        
        if filters.brand:
            results = [
                p for p in results
                if p.brand and p.brand.lower() == filters.brand.lower()
            ]
        
        # Attribute filters
        for attr_key, attr_value in filters.attributes.items():
            results = [
                p for p in results
                if attr_key in p.attributes and
                str(p.attributes[attr_key]).lower() == str(attr_value).lower()
            ]
        
        # Text search (basic keyword matching)
        if filters.search_query:
            search_terms = filters.search_query.lower().split()
            results = [
                p for p in results
                if self._matches_search(p, search_terms)
            ]
        
        # Apply soft filters (scoring) if preferred features are specified
        if filters.preferred_features:
            results = self._score_and_sort(results, filters.preferred_features)
        
        # Pagination
        start = filters.offset
        end = start + filters.limit
        
        return results[start:end]
    
    def _matches_search(self, product: Product, search_terms: List[str]) -> bool:
        """
        Check if product matches search terms.
        
        Args:
            product: Product to check
            search_terms: List of search terms (lowercase)
            
        Returns:
            True if product matches
        """
        # Searchable fields
        searchable_text = ' '.join([
            product.name or '',
            product.description or '',
            product.brand or '',
            ' '.join(product.features),
            ' '.join(str(v) for v in product.attributes.values())
        ]).lower()
        
        # Check if all search terms are present
        return all(term in searchable_text for term in search_terms)
    
    def _score_and_sort(self, products: List[Product], preferred_features: List[str]) -> List[Product]:
        """
        Score products based on preferred features and sort by score.
        
        Args:
            products: List of products to score
            preferred_features: Features to boost
            
        Returns:
            Sorted list of products
        """
        scored_products = []
        
        for product in products:
            score = 0
            
            # Score based on feature matches
            product_features_lower = [f.lower() for f in product.features]
            for pref_feature in preferred_features:
                pref_lower = pref_feature.lower()
                if pref_lower in product_features_lower:
                    score += 2
                elif any(pref_lower in f for f in product_features_lower):
                    score += 1
            
            # Score based on attribute matches
            for attr_value in product.attributes.values():
                attr_value_lower = str(attr_value).lower()
                for pref_feature in preferred_features:
                    if pref_feature.lower() in attr_value_lower:
                        score += 1
            
            scored_products.append((score, product))
        
        # Sort by score (descending) and return products
        scored_products.sort(key=lambda x: x[0], reverse=True)
        return [p for _, p in scored_products]
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get catalog statistics.
        
        Returns:
            Dictionary with catalog stats
        """
        if not self.products:
            return {
                'total_products': 0,
                'categories': [],
                'brands': [],
                'price_range': None
            }
        
        categories = set(p.category for p in self.products)
        brands = set(p.brand for p in self.products if p.brand)
        
        prices = [p.price for p in self.products if p.price is not None]
        price_range = {
            'min': min(prices) if prices else None,
            'max': max(prices) if prices else None,
            'avg': sum(prices) / len(prices) if prices else None
        }
        
        return {
            'total_products': len(self.products),
            'categories': sorted(categories),
            'brands': sorted(brands),
            'price_range': price_range
        }
    
    def is_loaded(self) -> bool:
        """Check if catalog has been loaded."""
        return self._loaded


# Global catalog instance (singleton pattern for POC)
_catalog_instance: Optional[ProductCatalog] = None


def get_catalog() -> ProductCatalog:
    """
    Get the global catalog instance.
    
    Returns:
        ProductCatalog instance
    """
    global _catalog_instance
    if _catalog_instance is None:
        _catalog_instance = ProductCatalog()
    return _catalog_instance


# Convenience functions

def load_products_from_json(path: str) -> int:
    """Load products into the global catalog."""
    catalog = get_catalog()
    return catalog.load_products_from_json(path)


def filter_products(filters: Optional[ProductFilter] = None, **kwargs) -> List[Product]:
    """Filter products from the global catalog."""
    catalog = get_catalog()
    return catalog.filter_products(filters, **kwargs)


def get_product_by_id(product_id: str) -> Optional[Product]:
    """Get a product by ID from the global catalog."""
    catalog = get_catalog()
    return catalog.get_product_by_id(product_id)
