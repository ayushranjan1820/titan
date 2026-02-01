// API service for making HTTP requests

import config from '../config';

class ApiService {
    constructor() {
        this.baseUrl = config.apiBaseUrl;
    }

    async request(endpoint, options = {}) {
        const url = `${this.baseUrl}${endpoint}`;

        const defaultOptions = {
            headers: {
                'Content-Type': 'application/json',
            },
        };

        const finalOptions = { ...defaultOptions, ...options };

        try {
            const response = await fetch(url, finalOptions);

            if (!response.ok) {
                const error = await response.json().catch(() => ({ detail: 'Request failed' }));
                throw new Error(error.detail || `HTTP ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error(`API request failed: ${url}`, error);
            throw error;
        }
    }

    // Health check
    async healthCheck() {
        return this.request(config.endpoints.health);
    }

    // Get products with filters
    async getProducts(filters = {}) {
        const params = new URLSearchParams();

        Object.entries(filters).forEach(([key, value]) => {
            if (value !== null && value !== undefined && value !== '') {
                params.append(key, value);
            }
        });

        const queryString = params.toString();
        const endpoint = `${config.endpoints.products}${queryString ? '?' + queryString : ''}`;

        return this.request(endpoint);
    }

    // Get single product
    async getProduct(productId) {
        return this.request(config.endpoints.productDetail(productId));
    }

    // Get catalog stats
    async getCatalogStats() {
        return this.request(config.endpoints.catalogStats);
    }

    // Chat recommendation
    async chatRecommend(userQuery, userPreferences = null) {
        return this.request(config.endpoints.chatRecommend, {
            method: 'POST',
            body: JSON.stringify({
                user_query: userQuery,
                user_preferences: userPreferences,
            }),
        });
    }
}

const apiService = new ApiService();
export default apiService;
