// API configuration

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

export const config = {
    apiBaseUrl: API_BASE_URL,
    endpoints: {
        health: '/health',
        products: '/products',
        productDetail: (id) => `/products/${id}`,
        chatRecommend: '/chat/recommend',
        catalogStats: '/catalog/stats',
    },
};

export default config;
