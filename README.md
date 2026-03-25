# pothole_monitor

A pothole detection system using AI (TensorFlow), FastAPI, Firebase Firestore, and OpenStreetMap.

---

## Architecture

- **Backend**: FastAPI + TensorFlow model (`pothole_model.h5`) hosted on Railway
- **Frontend**: Static HTML/CSS/JavaScript with Leaflet.js + OpenStreetMap, hosted on GitHub Pages / Vercel
- **Database**: Firebase Firestore (cloud) — stores detected pothole coordinates and confidence scores

---

## How it works

1. User takes a photo via the frontend
2. The browser gets the GPS coordinates and sends the image + location to the backend (`/predict/` endpoint)
3. The backend runs the image through the TensorFlow model
4. If confidence > 50%, the pothole is saved to Firestore
5. The map page polls `/potholes` and displays markers for all detected potholes

---

## Deployment

### Backend (Railway)

1. Push `main.py`, `requirements.txt`, and `pothole_model.h5` to GitHub
2. In Railway: **New Project** → **Deploy from GitHub repo**
3. Set the start command in the service settings:
   ```
   uvicorn main:app --host 0.0.0.0 --port $PORT
   ```
4. In the service **Variables** tab, add:
   - `FIREBASE_KEY` = paste the full contents of `firebase_key.json`
5. In service **Settings** → **Networking**, click **Generate Domain** to get a public URL

> `firebase_key.json` must never be committed to the repo. The app reads it from the `FIREBASE_KEY` environment variable.

### Frontend (GitHub Pages)

1. Ensure `js/script.js` and `js/map.js` point to the Railway URL (not `localhost`)
2. Push the frontend files to GitHub
3. Go to the repo → **Settings** → **Pages** → Source: `main` branch, `/ (root)` → Save
4. Site will be live at `https://YOUR_USERNAME.github.io/YOUR_REPO/`

---

## Local development

```bash
# Install dependencies
pip install -r requirements.txt

# Run backend (requires firebase_key.json in project root)
uvicorn main:app --reload
```

The frontend can be opened directly in a browser (`index.html`, `map.html`).

---

## Files

| File | Description |
|---|---|
| `main.py` | FastAPI backend with `/predict/` and `/potholes` endpoints |
| `pothole_model.h5` | Trained TensorFlow binary classifier |
| `requirements.txt` | Python dependencies |
| `index.html` | Photo capture UI |
| `map.html` | Map view with pothole markers |
| `js/script.js` | Handles photo upload and prediction request |
| `js/map.js` | Loads and displays potholes on the map |
