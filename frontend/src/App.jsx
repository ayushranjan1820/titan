import React, { useState } from 'react';
import ProductList from './components/ProductList';
import ChatPanel from './components/ChatPanel';
import VirtualTryOn from './components/VirtualTryOn';
import './App.css';

/**
 * Main App Component
 * Manages state and navigation between product list, chat, and virtual try-on
 */
function App() {
  const [view, setView] = useState('main'); // 'main' or 'try-on'
  const [selectedProduct, setSelectedProduct] = useState(null);
  const [recommendedProducts, setRecommendedProducts] = useState([]);
  const [isChatOpen, setIsChatOpen] = useState(false);

  // Handle Try On button click
  const handleTryOn = (product) => {
    setSelectedProduct(product);
    setView('try-on');
  };

  // Handle chat recommendations
  const handleRecommendation = (response) => {
    setRecommendedProducts(response.products || []);
  };

  // Handle product click from chat recommendations
  const handleProductClick = (product) => {
    setIsChatOpen(false);
    handleTryOn(product);
  };

  // Handle close try-on
  const handleCloseTryOn = () => {
    setView('main');
    setSelectedProduct(null);
  };

  return (
    <div className="app">
      {view === 'main' ? (
        <>
          {/* Header */}
          <header className="app-header">
            <div className="header-content">
              <h1>Virtual Try-On</h1>
              <p>Find your perfect watch with AI-powered recommendations</p>
            </div>
          </header>

          {/* Main Content - Full Width */}
          <div className="app-content app-content-full">
            <ProductList
              onTryOn={handleTryOn}
              initialFilters={recommendedProducts.length > 0 ? {} : {}}
            />
          </div>

          {/* Floating Chat Button */}
          <button
            className="floating-chat-button"
            onClick={() => setIsChatOpen(true)}
            aria-label="Open chat"
          >
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
            </svg>
            <span className="chat-badge">AI</span>
          </button>

          {/* Chat Modal */}
          {isChatOpen && (
            <div className="chat-modal-overlay" onClick={() => setIsChatOpen(false)}>
              <div className="chat-modal" onClick={(e) => e.stopPropagation()}>
                <button
                  className="chat-close-button"
                  onClick={() => setIsChatOpen(false)}
                >
                  ✕
                </button>
                <ChatPanel
                  onRecommendation={handleRecommendation}
                  onProductClick={handleProductClick}
                />
              </div>
            </div>
          )}

          {/* Footer */}
          <footer className="app-footer">
            <p>Virtual Try-On POC • Built with React + FastAPI + MediaPipe</p>
          </footer>
        </>
      ) : (
        /* Virtual Try-On View */
        <VirtualTryOn
          product={selectedProduct}
          onClose={handleCloseTryOn}
        />
      )}
    </div>
  );
}

export default App;
