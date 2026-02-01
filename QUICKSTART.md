Get the Virtual Try-On POC

## Prerequisites

- **Python 3.9+** ([Download](https://www.python.org/downloads/))
- **Node.js 16+** ([Download](https://nodejs.org/))
- **Git** (optional)

## Step 1: Download/Clone

If using Git:
```bash
git clone <your-repo-url>
cd titan
```

## Step 2: Automated Setup

```bash
chmod +x setup.sh
./setup.sh
```

This will:
- Create Python virtual environment
- Install all Python dependencies
- Install npm dependencies
- Create `.env` files from templates

## Step 3: Configure LLM (Optional)

For AI-powered recommendations, add your API key to `backend/.env`:

```bash
# Edit backend/.env
# Add ONE of the following:
OPENAI_API_KEY=sk-your-key-here
# OR
GOOGLE_API_KEY=your-gemini-key-here
```

> **Note**: The POC works without an LLM API key (uses mock responses)

## Step 4: Start Everything

```bash
chmod +x start.sh
./start.sh
```

This launches:
- **Backend API** at http://localhost:8000
- **Frontend** at http://localhost:5173

## Step 5: Open in Browser

Navigate to: **http://localhost:5173**

---

## 🎯 What You Can Do

### 1. Browse Products
- Use filters (price, gender, style)
- Search for products

### 2. Chat Recommendations
- Ask: "I need a formal watch for a wedding under 10000"
- See AI-powered recommendations

### 3. Virtual Try-On
- Click "Try On" on any product
- Allow camera accesss
- Position your wrist in view
- See the watch overlaid on your wrist

---

## 📊 Example API Calls

### Health Check
```bash
curl http://localhost:8000/health
```

### List Products
```bash
curl "http://localhost:8000/products?limit=5"
```

### Filter Products
```bash
curl "http://localhost:8000/products?max_price=10000&gender=Men&style=Formal"
```

### Chat Recommendation
```bash
curl -X POST http://localhost:8000/chat/recommend \
  -H "Content-Type: application/json" \
  -d '{"user_query": "formal watch under 10000"}'
```

### API Documentation
Open: http://localhost:8000/docs

---

## 🔧 Development Commands

### Backend

```bash
# Activate virtual environment
cd backend
source venv/bin/activate  # mac/linux
# OR
venv\Scripts\activate     # windows

# Run server
uvicorn app.main:app --reload

# Run tests
python test_api.py
```

### Frontend

```bash
cd frontend

# Development server
npm run dev

# Build for production
npm run build

# Preview build
npm run preview
```

### Scraper

```bash
cd scraper
source ../backend/venv/bin/activate

# Dry run (validate config)
python src/run_scraper.py \
  --config config/watches_site_template.yaml \
  --dry-run

# Scrape products
python src/run_scraper.py \
  --config config/watches_site_template.yaml \
  --limit 100 \
  --output ../data/products_watches.json
```

---

## 🐛 Troubleshooting

### Port Already in Use

**Backend (8000)**:
```bash
# Find process
lsof -i :8000
# Kill it
kill -9 <PID>
```

**Frontend (5173)**:
```bash
# Find process
lsof -i :5173
# Kill it
kill -9 <PID>
```

### Camera Not Working

1. Check browser permissions (allow camera access)
2. Use HTTPS (or localhost)
3. Try standalone try-on: `virtual_try_on/web/index.html`

### LLM Not Working

- Check `.env` file has correct API key
- Check API key validity
- POC works with mock responses if no key

### Products Not Loading

1. Check if `data/products_watches.json` exists
2. Run scraper to generate data
3. Check backend logs for errors

---

## 📁 Project Structure

```
titan/
├── backend/         # FastAPI server
├── frontend/        # React app
├── scraper/         # Web scraper
├── data/            # Product JSON
├── virtual_try_on/  # Standalone AR
├── setup.sh         # Setup script
└── start.sh         # Start script
```

---

## 🎓 Learn More

- **[README.md](file:///Users/ayushranjan/Developer/titan/README.md)** - Full documentation
- **[Walkthrough](file:///Users/ayushranjan/.gemini/antigravity/brain/4bfbe204-bc78-4521-8e07-efa080ff7204/walkthrough.md)** - Implementation details
- **API Docs** - http://localhost:8000/docs

---

## 🤝 Support

For issues or questions:
1. Check the README.md
2. Check the walkthrough.md
3. Review error logs in terminal

---