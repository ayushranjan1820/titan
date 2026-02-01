import React, { useState, useRef, useEffect } from 'react';
import './ChatPanel.css';
import apiService from '../services/api';

/**
 * ChatPanel Component
 * Conversational interface for product recommendations
 */
function ChatPanel({ onRecommendation, onProductClick }) {
    const [messages, setMessages] = useState([
        {
            role: 'assistant',
            content: '👋 Hi! I can help you find the perfect watch. Tell me what you\'re looking for!',
        },
    ]);
    const [inputValue, setInputValue] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const messagesEndRef = useRef(null);

    // Auto-scroll to bottom
    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages]);

    const handleSubmit = async (e) => {
        e?.preventDefault();

        if (!inputValue.trim() || isLoading) return;

        const userMessage = inputValue.trim();
        setInputValue('');

        // Add user message
        setMessages(prev => [
            ...prev,
            { role: 'user', content: userMessage },
        ]);

        setIsLoading(true);

        try {
            // Call recommendation API
            const response = await apiService.chatRecommend(userMessage);

            // Add assistant response
            setMessages(prev => [
                ...prev,
                {
                    role: 'assistant',
                    content: response.llm_explanation,
                    data: {
                        query_understanding: response.query_understanding,
                        products: response.products,
                        total_matches: response.total_matches,
                    },
                },
            ]);

            // Notify parent component about recommendations
            if (onRecommendation) {
                onRecommendation(response);
            }

        } catch (error) {
            // Add error message with simplified, user-friendly text
            const errorMessage = error.message.includes('Recommendation failed')
                ? 'Sorry, I encountered an issue processing your request. Please try rephrasing your query.'
                : error.message.includes('Network') || error.message.includes('fetch')
                    ? 'Unable to connect to the server. Please check your connection and try again.'
                    : 'Something went wrong. Please try again.';

            setMessages(prev => [
                ...prev,
                {
                    role: 'assistant',
                    content: `❌ ${errorMessage}`,
                    isError: true,
                },
            ]);

            // Log full error for debugging (console only)
            console.error('Chat error:', error);
        } finally {
            setIsLoading(false);
        }
    };

    const handleKeyPress = (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSubmit();
        }
    };

    return (
        <div className="chat-panel">
            {/* Header */}
            <div className="chat-header">
                <h3>💬 Chat Assistant</h3>
                <p>Ask me anything about watches!</p>
            </div>

            {/* Messages */}
            <div className="chat-messages">
                {messages.map((message, index) => (
                    <div key={index} className={`message message-${message.role}`}>
                        <div className="message-content">
                            {message.content}
                        </div>

                        {/* Show product recommendations if available */}
                        {message.data?.products && message.data.products.length > 0 && (
                            <div className="message-recommendations">
                                <div className="recommendations-header">
                                    <strong>Found {message.data.total_matches} matches</strong>
                                    <span className="recommendations-subtitle">
                                        Showing top {message.data.products.length}
                                    </span>
                                </div>

                                {/* Mini product cards */}
                                <div className="mini-products-list">
                                    {message.data.products.slice(0, 3).map((product) => (
                                        <div
                                            key={product.id}
                                            className="mini-product-card"
                                            onClick={() => onProductClick && onProductClick(product)}
                                            style={{ cursor: 'pointer' }}
                                        >
                                            {product.image_url && (
                                                <img
                                                    src={product.image_url}
                                                    alt={product.name}
                                                    className="mini-product-image"
                                                />
                                            )}
                                            <div className="mini-product-info">
                                                <div className="mini-product-name">{product.name}</div>
                                                <div className="mini-product-price">
                                                    ₹{product.price?.toLocaleString('en-IN')}
                                                </div>
                                            </div>
                                            <div className="try-on-hint">👁️ Try On</div>
                                        </div>
                                    ))}
                                </div>

                                {/* Filters applied */}
                                {message.data.query_understanding && (
                                    <div className="applied-filters">
                                        <strong>Understood filters:</strong>
                                        <div className="filter-tags">
                                            {Object.entries(message.data.query_understanding).map(([key, value]) => {
                                                if (value && key !== 'additional_preferences' && key !== 'search_query') {
                                                    return (
                                                        <span key={key} className="filter-tag">
                                                            {key}: {JSON.stringify(value)}
                                                        </span>
                                                    );
                                                }
                                                return null;
                                            })}
                                        </div>
                                    </div>
                                )}
                            </div>
                        )}
                    </div>
                ))}

                {/* Loading indicator */}
                {isLoading && (
                    <div className="message message-assistant">
                        <div className="message-content">
                            <div className="typing-indicator">
                                <span></span>
                                <span></span>
                                <span></span>
                            </div>
                        </div>
                    </div>
                )}

                <div ref={messagesEndRef} />
            </div>

            {/* Input */}
            <form onSubmit={handleSubmit} className="chat-input-form">
                <input
                    type="text"
                    placeholder="E.g., I need a formal watch for a wedding under ₹10,000"
                    value={inputValue}
                    onChange={(e) => setInputValue(e.target.value)}
                    onKeyPress={handleKeyPress}
                    className="chat-input"
                    disabled={isLoading}
                />
                <button
                    type="submit"
                    disabled={!inputValue.trim() || isLoading}
                    className="chat-send-button"
                >
                    ➤
                </button>
            </form>
        </div>
    );
}

export default ChatPanel;
