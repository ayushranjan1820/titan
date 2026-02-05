# 3D Watch Models Setup Guide

## Required Models

We need 3 glTF watch models for the following products:

1. **Titan Raga Viva** → `titan_raga_viva.glb`
2. **Titan Edge Ceramic** → `titan_edge_ceramic.glb`
3. **Fastrack Reflex** → `fastrack_reflex.glb`

---

## How to Source Models

### Option 1: Download from Sketchfab (Recommended)

1. Go to [Sketchfab](https://sketchfab.com)
2. Search for: "wristwatch", "analog watch", "watch"
3. Filter by:
   - **Downloadable**: Yes
   - **Format**: glTF  
   - **License**: Creative Commons (for free use)

4. Look for models with:
   - Round dial shape
   - Standard strap (leather or metal band)
   - Separated strap and face components (check model preview)
   - Reasonable polygon count (<10k triangles)

5. Download as `.glb` format
6. Rename to match the filenames above
7. Place in `frontend/public/models/`

### Option 2: Create Simple Models in Blender

If you can't find suitable models:

1. Open Blender
2. Create basic watch geometry:
   - Cylinder for watch face
   - Torus for bezel
   - Extruded curves for strap
3. Export as glTF 2.0 Binary (.glb)

---

## Model Requirements

✅ **Must have:**
- Format: `.glb` (binary glTF)
- Separated objects: `watch_face` and `strap` (or `band`)
- Reasonable size (<5MB per model)
- Proper UV mapping for textures

✅ **Recommended:**
- Poly count: <10k triangles per model
- Texture resolution: 1024x1024 max
- PBR materials (Metallic/Roughness workflow)

---

## Testing Without Models

For testing the 3D infrastructure without actual models, you can:

1. Use placeholder geometry (cubes/cylinders)
2. The code will gracefully handle missing models
3. Fall back to 2D rendering if 3D model fails to load

---

## Suggested Free Watch Models

Here are some specific Sketchfab models you can use:

1. **Search:** "analog wristwatch" → Look for leather strap watches
2. **Search:** "watch glb" → Filter by downloadable
3. **Search:** "wrist watch free" → Check Creative Commons licenses

Example models (as of 2024):
- [Simple Watch by user] - Round dial with leather strap
- [Classic Wristwatch] - Metal band chronograph style
- [Fitness Band] - Sport/casual design

---

## Installation

Once you have the models:

```bash
# From project root
mkdir -p frontend/public/models

# Copy your downloaded .glb files
cp path/to/titan_raga_viva.glb frontend/public/models/
cp path/to/titan_edge_ceramic.glb frontend/public/models/
cp path/to/fastrack_reflex.glb frontend/public/models/
```

Verify the files are in place:
```bash
ls -lh frontend/public/models/
```

You should see:
```
titan_raga_viva.glb
titan_edge_ceramic.glb
fastrack_reflex.glb
```

---

## Next Steps

After placing models:
1. Restart the frontend dev server
2. Navigate to one of the 3 flagged products
3. Click "Try On"
4. The 3D renderer should automatically activate

Check console for:
- `📦 Loading 3D model: /models/[filename].glb`
- `✅ 3D model loaded successfully`
- `🎨 Found X strap meshes for deformation`
