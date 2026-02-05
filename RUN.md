# How to Run the Virtual Try-On Application

## Quick Start (Recommended)

The easiest way to run the application is using the startup script:

```bash
./start.sh
```

This script will:
- ✅ Create Python virtual environment (if needed)
- ✅ Install all backend dependencies automatically
- ✅ Install all frontend dependencies automatically
- ✅ Start both backend and frontend servers
- ✅ Handle graceful shutdown with Ctrl+C

Once running, open your browser to **http://localhost:5173**

---

## Manual Setup (Alternative)

If you prefer to run servers separately or need more control:

### Step 1: Backend Setup

```bash
# Navigate to backend directory
cd backend

# Create virtual environment (first time only)
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate  # On macOS/Linux
# OR
venv\Scripts\activate     # On Windows

# Install dependencies (first time only)
pip install -r requirements.txt

# Start backend server
uvicorn app.main:app --reload
```

The backend will run on **http://localhost:8000**
- API documentation: http://localhost:8000/docs

### Step 2: Frontend Setup

Open a **new terminal window** and run:

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies (first time only)
npm install

# Start development server
npm run dev
```

The frontend will run on **http://localhost:5173**

---

## Using the Virtual Try-On Feature

1. **Open the application** at http://localhost:5173
2. **Browse watches** from the product listing
3. **Click "Try On"** on any watch
4. **Allow camera access** when prompted by your browser
5. **Hold your wrist** in front of the camera
6. **Watch the magic!** The watch will overlay on your wrist with:
   - ✨ White background removed (transparent overlay)
   - ✨ 3D shadow effects for depth
   - ✨ Natural rotation aligned with your wrist
   - ✨ Realistic sizing (85% of wrist width)

### Tips for Best Results:
- Ensure good lighting
- Hold your wrist steady in front of the camera
- Position your entire hand in the camera frame
- The watch will track your wrist movement in real-time

---

## Latest Enhancements

The virtual try-on feature now includes:

### 🎯 Fixed Watch Orientation
- Watch face is now perpendicular to your forearm (like a real watch)
- Uses multiple hand landmarks (wrist, index, middle, pinky) for accurate alignment
- Maintains natural appearance across all wrist angles

### 📏 Improved Watch Size
- Increased from 55% to **85% of hand width** for realistic visibility
- Properly proportioned to match real watch dimensions
- More prominent and easier to see on screen

### 🎨 Visual Quality
- Transparent background (white removed via chroma key)
- Drop shadow for 3D depth effect
- Smooth real-time tracking

---

## Troubleshooting

### Backend won't start
```bash
# Make sure you're in the virtual environment
cd backend
source venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt

# Try starting again
uvicorn app.main:app --reload
```

### Frontend won't start
```bash
# Clear node_modules and reinstall
cd frontend
rm -rf node_modules package-lock.json
npm install
npm run dev
```

### Camera not working
- Check browser permissions (allow camera access)
- Try a different browser (Chrome/Firefox recommended)
- Ensure no other application is using the camera

### Products not loading
- Verify backend is running on port 8000
- Check backend logs for errors
- Visit http://localhost:8000/docs to test API

---

## Stopping the Application

### If using start.sh:
Press **Ctrl+C** in the terminal running the script

### If running manually:
Press **Ctrl+C** in each terminal window (backend and frontend)

---

## Environment Requirements

- **Python**: 3.8+ (for backend)
- **Node.js**: 16+ (for frontend)
- **npm**: 7+ (comes with Node.js)
- **Modern browser** with camera support (Chrome, Firefox, Safari, Edge)

---

## Next Steps

After running the application:
1. Test the virtual try-on with different watches
2. Try different wrist angles and positions
3. Check the console for any errors or warnings
4. Explore the chat-based product recommendation feature (coming soon)
