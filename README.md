# Virtual Try-On + Product Recommendation POC

An end-to-end proof of concept for a conversational product recommendation system with virtual try-on capability.

## 🎯 Overview

This POC demonstrates:
- **Config-driven web scraping** for e-commerce product data
- **Conversational AI** for natural language product recommendations
- **Virtual try-on** using computer vision and AR overlay
- **Generalizable architecture** for multiple product categories

### Tech Stack
- **Backend**: Python + FastAPI
- **Frontend**: React.js
- **Scraping**: Python (httpx, BeautifulSoup, Playwright)
- **LLM/RAG**: OpenAI/Gemini API integration
- **Virtual Try-On**: MediaPipe Hands + Canvas API

## 📁 Project Structure

```
titan/
├── scraper/              # Web scraping module
│   ├── config/          # Site-specific scraping configs
│   └── src/             # Scraper core logic
├── backend/             # FastAPI backend
│   ├── app/            # API routes and main app
│   ├── models/         # Data models (Pydantic)
│   └── services/       # Business logic (catalog, NLP, recommendations)
├── frontend/            # React frontend
│   └── src/
│       └── components/ # React components
├── virtual_try_on/      # Virtual try-on module
│   └── web/            # Standalone HTML/JS implementation
├── data/                # Scraped product data (JSON)
└── notebooks/           # Jupyter notebooks for exploration
```

## 🚀 Quick Start

### Prerequisites
- Python 3.9+
- Node.js 16+
- npm or yarn

### 1. Backend Setup

```bash
# Create virtual environment
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the API server
uvicorn app.main:app --reload

# API will be available at http://localhost:8000
# API docs at http://localhost:8000/docs
```

### 2. Scraper Setup

```bash
# From project root
cd scraper

# Run scraper with config
python src/run_scraper.py --config config/watches_site_template.yaml --limit 100

# Output: data/products_watches.json
```

### 3. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Run development server
npm run dev

# Frontend will be available at http://localhost:5173
```

## 📖 Usage Examples

### Scraping Products

```bash
# Scrape watches
python scraper/src/run_scraper.py \
  --config scraper/config/watches_site_template.yaml \
  --limit 500

# Scrape another category (e.g., grocery)
python scraper/src/run_scraper.py \
  --config scraper/config/grocery_site_template.yaml \
  --limit 200
```

### API Endpoints

```bash
# Health check
curl http://localhost:8000/health

# List products with filters
curl "http://localhost:8000/products?max_price=10000&gender=men&style=formal"

# Get single product
curl http://localhost:8000/products/watch-123

# Chat recommendation
curl -X POST http://localhost:8000/chat/recommend \
  -H "Content-Type: application/json" \
  -d '{
    "user_query": "I need a formal mens watch for a wedding under 10000 rupees"
  }'
```

### Virtual Try-On

1. Navigate to the virtual try-on page in the frontend
2. Click "Try On" on any product
3. Allow camera access
4. Position your wrist in front of the camera
5. The watch will overlay on your wrist in real-time

## 🔧 Configuration

### Scraper Configuration

Create a YAML config file in `scraper/config/`:

```yaml
site_name: "Example E-commerce Site"
category: "watches"
start_urls:
  - "https://example.com/watches?page=1"
pagination:
  type: "url_param"
  param_name: "page"
  max_pages: 20
selectors:
  product_links: "div.product-card a.product-link"
  product_detail:
    name: "h1.product-title"
    price: "span.price"
    brand: "span.brand"
    # ... more selectors
```

### Environment Variables

Create a `.env` file in the `backend/` directory:

```env
# LLM API Configuration
OPENAI_API_KEY=your_key_here
# OR
GOOGLE_API_KEY=your_gemini_key_here

# Database (optional)
DATABASE_URL=sqlite:///./products.db
```

## 🧩 Adding a New Product Category

1. **Create scraper config**: `scraper/config/your_category.yaml`
2. **Define category-specific attributes** in the config
3. **Update LLM prompts** in `backend/services/nlp.py` if needed
4. **Run scraper**: `python scraper/src/run_scraper.py --config config/your_category.yaml`

The system is designed to be category-agnostic!

## 📚 Architecture

### Data Flow

```
User Query
    ↓
Frontend (React)
    ↓
Backend API (FastAPI)
    ↓
NLP Service → LLM API
    ↓
Recommendation Service
    ↓
Product Catalog
    ↓
Response with Products
    ↓
Frontend Display + Virtual Try-On
```

### Key Components

1. **Scraper**: Config-driven, site-agnostic product data extraction
2. **Product Catalog**: In-memory catalog with filtering and search
3. **NLP Service**: Query parsing and filter extraction using LLM
4. **Recommendation Engine**: Hybrid filtering (hard + soft) and RAG
5. **Virtual Try-On**: MediaPipe hand tracking + canvas overlay

## 🧪 Testing

```bash
# Test scraper
python scraper/src/run_scraper.py --config scraper/config/watches_site_template.yaml --limit 10

# Test backend
pytest backend/tests/

# Start backend and test endpoints
curl http://localhost:8000/health
curl http://localhost:8000/products

# Test frontend
cd frontend && npm test
```

## 🎨 Virtual Try-On Details

The virtual try-on module uses:
- **MediaPipe Hands** for real-time hand/wrist detection
- **Canvas API** for overlay rendering
- **Keypoint tracking** for position, scale, and rotation

### How It Works
1. Detect hand keypoints (21 landmarks per hand)
2. Identify wrist position (landmark 0)
3. Calculate scale based on hand size (wrist to middle knuckle distance)
4. Calculate rotation based on hand orientation
5. Overlay watch image with transformations

## 🔮 Future Enhancements

- [ ] Database integration (PostgreSQL/MongoDB)
- [ ] Vector database for semantic search (Qdrant/Faiss)
- [ ] Advanced RAG with embeddings
- [ ] User authentication and preferences
- [ ] Multi-angle virtual try-on (3D models)
- [ ] Mobile app (React Native)
- [ ] Deployment (Docker + Kubernetes)

## 📝 License

This is a POC project. For production use, ensure compliance with:
- Web scraping target site's TOS
- LLM API usage policies
- Privacy regulations for camera/image processing

## 🤝 Contributing

This is a POC template. Feel free to extend and adapt for your use case!

---

**Built with ❤️ for the Titan GenAI Chatbot Project**
