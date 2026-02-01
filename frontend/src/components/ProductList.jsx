import React, { useState, useEffect } from 'react';
import ProductCard from './ProductCard';
import './ProductList.css';
import apiService from '../services/api';

/**
 * ProductList Component
 * Displays a grid of products with filtering options
 */
function ProductList({ onTryOn, initialFilters = {} }) {
    const [products, setProducts] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [filters, setFilters] = useState({
        search: '',
        min_price: '',
        max_price: '',
        gender: '',
        style: '',
        ...initialFilters,
    });

    // Load products
    useEffect(() => {
        loadProducts();
    }, []);

    const loadProducts = async (customFilters = null) => {
        try {
            setLoading(true);
            setError(null);

            const appliedFilters = customFilters || filters;
            const data = await apiService.getProducts(appliedFilters);

            setProducts(data);
        } catch (err) {
            setError(err.message);
            console.error('Failed to load products:', err);
        } finally {
            setLoading(false);
        }
    };

    const handleFilterChange = (name, value) => {
        setFilters(prev => ({
            ...prev,
            [name]: value,
        }));
    };

    const handleApplyFilters = () => {
        loadProducts();
    };

    const handleClearFilters = () => {
        const clearedFilters = {
            search: '',
            min_price: '',
            max_price: '',
            gender: '',
            style: '',
        };
        setFilters(clearedFilters);
        loadProducts(clearedFilters);
    };

    return (
        <div className="product-list-container">
            {/* Filters */}
            <div className="filters-bar">
                <h2>Products</h2>

                <div className="filters-grid">
                    {/* Search */}
                    <input
                        type="text"
                        placeholder="Search products..."
                        value={filters.search}
                        onChange={(e) => handleFilterChange('search', e.target.value)}
                        className="filter-input"
                        onKeyPress={(e) => e.key === 'Enter' && handleApplyFilters()}
                    />

                    {/* Price Range */}
                    <div className="filter-group">
                        <input
                            type="number"
                            placeholder="Min Price"
                            value={filters.min_price}
                            onChange={(e) => handleFilterChange('min_price', e.target.value)}
                            className="filter-input filter-input-small"
                        />
                        <span className="filter-separator">-</span>
                        <input
                            type="number"
                            placeholder="Max Price"
                            value={filters.max_price}
                            onChange={(e) => handleFilterChange('max_price', e.target.value)}
                            className="filter-input filter-input-small"
                        />
                    </div>

                    {/* Gender */}
                    <select
                        value={filters.gender}
                        onChange={(e) => handleFilterChange('gender', e.target.value)}
                        className="filter-select"
                    >
                        <option value="">All Genders</option>
                        <option value="Men">Men</option>
                        <option value="Women">Women</option>
                        <option value="Unisex">Unisex</option>
                    </select>

                    {/* Style */}
                    <select
                        value={filters.style}
                        onChange={(e) => handleFilterChange('style', e.target.value)}
                        className="filter-select"
                    >
                        <option value="">All Styles</option>
                        <option value="Formal">Formal</option>
                        <option value="Casual">Casual</option>
                        <option value="Sport">Sport</option>
                        <option value="Elegant">Elegant</option>
                    </select>

                    {/* Action Buttons */}
                    <button onClick={handleApplyFilters} className="btn btn-primary">
                        Apply Filters
                    </button>
                    <button onClick={handleClearFilters} className="btn btn-secondary">
                        Clear
                    </button>
                </div>
            </div>

            {/* Loading State */}
            {loading && (
                <div className="loading-state">
                    <div className="spinner"></div>
                    <p>Loading products...</p>
                </div>
            )}

            {/* Error State */}
            {error && (
                <div className="error-state">
                    <p>❌ {error}</p>
                    <button onClick={() => loadProducts()} className="btn btn-primary">
                        Retry
                    </button>
                </div>
            )}

            {/* Empty State */}
            {!loading && !error && products.length === 0 && (
                <div className="empty-state">
                    <p>No products found. Try adjusting your filters.</p>
                </div>
            )}

            {/* Products Grid */}
            {!loading && !error && products.length > 0 && (
                <>
                    <div className="products-header">
                        <p>{products.length} products found</p>
                    </div>

                    <div className="products-grid">
                        {products.map((product) => (
                            <ProductCard
                                key={product.id}
                                product={product}
                                onTryOn={onTryOn}
                            />
                        ))}
                    </div>
                </>
            )}
        </div>
    );
}

export default ProductList;
