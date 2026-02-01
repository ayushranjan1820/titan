import React from 'react';
import './ProductCard.css';

/**
 * ProductCard Component
 * Displays a single product with image, details, and actions
 */
function ProductCard({ product, onTryOn }) {
    const {
        id,
        name,
        description,
        price,
        currency = 'INR',
        brand,
        image_url,
        attributes = {},
        features = [],
    } = product;

    // Format price
    const formattedPrice = price
        ? new Intl.NumberFormat('en-IN', {
            style: 'currency',
            currency: currency,
            maximumFractionDigits: 0,
        }).format(price)
        : 'Price not available';

    return (
        <div className="product-card">
            {/* Product Image */}
            <div className="product-image-container">
                {image_url ? (
                    <img
                        src={image_url}
                        alt={name}
                        className="product-image"
                        onError={(e) => {
                            e.target.src = 'https://via.placeholder.com/300x300?text=No+Image';
                        }}
                    />
                ) : (
                    <div className="product-image-placeholder">
                        <span>No Image</span>
                    </div>
                )}

                {/* Quick action buttons */}
                <div className="product-overlay">
                    <button
                        className="try-on-button"
                        onClick={() => onTryOn && onTryOn(product)}
                    >
                        👁️ Try On
                    </button>
                </div>
            </div>

            {/* Product Details */}
            <div className="product-details">
                {/* Brand */}
                {brand && <div className="product-brand">{brand}</div>}

                {/* Name */}
                <h3 className="product-name">{name}</h3>

                {/* Price */}
                <div className="product-price">{formattedPrice}</div>

                {/* Attributes */}
                {Object.keys(attributes).length > 0 && (
                    <div className="product-attributes">
                        {attributes.gender && (
                            <span className="attribute-badge">{attributes.gender}</span>
                        )}
                        {attributes.style && (
                            <span className="attribute-badge">{attributes.style}</span>
                        )}
                    </div>
                )}

                {/* Description (truncated) */}
                {description && (
                    <p className="product-description">
                        {description.length > 100
                            ? `${description.substring(0, 100)}...`
                            : description}
                    </p>
                )}

                {/* Features (first 3) */}
                {features.length > 0 && (
                    <ul className="product-features">
                        {features.slice(0, 3).map((feature, index) => (
                            <li key={index}>{feature}</li>
                        ))}
                    </ul>
                )}
            </div>
        </div>
    );
}

export default ProductCard;
