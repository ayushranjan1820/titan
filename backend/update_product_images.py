#!/usr/bin/env python3
"""
Script to update product image URLs based on product attributes.
Maps products to appropriate watch images based on gender, style, and category.
"""

import json
import sys
from pathlib import Path

# Image mapping based on product attributes
IMAGE_MAPPING = {
    ("Men", "Formal"): "/images/watches/formal_mens_1.png",
    ("Men", "Formal", "gold"): "/images/watches/formal_mens_2.png",
    ("Men", "Casual"): "/images/watches/casual_mens_1.png",
    ("Men", "Sporty"): "/images/watches/sporty_chronograph_1.png",
    ("Women", "Formal"): "/images/watches/formal_womens_1.png",
    ("Women", "Casual"): "/images/watches/formal_womens_1.png",
    ("Unisex", "Sporty"): "/images/watches/smartwatch_1.png",
    ("smart-watches",): "/images/watches/smartwatch_1.png",
}

def get_image_for_product(product):
    """Determine the appropriate image for a product based on its attributes."""
    gender = product.get("attributes", {}).get("gender", "")
    style = product.get("attributes", {}).get("style", "")
    sub_category = product.get("sub_category", "")
    name_lower = product.get("name", "").lower()
    
    # Check for smartwatch/digital
    if sub_category == "smart-watches" or "smart" in name_lower or "digital" in name_lower:
        return IMAGE_MAPPING[("smart-watches",)]
    
    # Check for gold/luxury watches
    if "gold" in name_lower or "regalia" in name_lower or "grandmaster" in name_lower:
        if gender == "Men" and style == "Formal":
            return IMAGE_MAPPING[("Men", "Formal", "gold")]
    
    # Standard mapping
    key = (gender, style)
    if key in IMAGE_MAPPING:
        return IMAGE_MAPPING[key]
    
    # Fallback based on gender only
    if gender == "Men":
        return IMAGE_MAPPING[("Men", "Casual")]
    elif gender == "Women":
        return IMAGE_MAPPING[("Women", "Formal")]
    else:
        return IMAGE_MAPPING[("Unisex", "Sporty")]

def main():
    # Load products
    products_file = Path(__file__).parent.parent / "data" / "products_watches.json"
    
    with open(products_file, 'r') as f:
        data = json.load(f)
    
    # Update image URLs
    updated_count = 0
    for product in data["products"]:
        new_image_url = get_image_for_product(product)
        product["image_url"] = new_image_url
        updated_count += 1
    
    # Save updated data
    with open(products_file, 'w') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Updated {updated_count} products with image URLs")
    print(f"📁 Saved to: {products_file}")

if __name__ == "__main__":
    main()
