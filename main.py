# -*- coding: utf-8 -*-
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
import tensorflow as tf
import numpy as np
import cv2
import firebase_admin
from firebase_admin import credentials, firestore
import os
import json
from ultralytics import YOLO

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load TensorFlow model
tf_model = tf.keras.models.load_model("pothole_model.h5")

# Load YOLO model
yolo_model = YOLO("PotholeTestModel.pt")

# Firebase config
firebase_key = json.loads(os.environ["FIREBASE_KEY"])
cred = credentials.Certificate(firebase_key)
firebase_admin.initialize_app(cred)
db = firestore.client()

IMG_SIZE = 128

def preprocess_tf(image_bytes):
    npimg = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(npimg, cv2.IMREAD_COLOR)
    img = cv2.resize(img, (IMG_SIZE, IMG_SIZE))
    img = img / 255.0
    img = np.expand_dims(img, axis=0)
    return img

def run_yolo(image_bytes):
    npimg = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(npimg, cv2.IMREAD_COLOR)
    h, w = img.shape[:2]
    results = yolo_model(img)[0]
    detections = []
    for box in results.boxes:
        x1, y1, x2, y2 = box.xyxy[0].tolist()
        conf = float(box.conf[0])
        detections.append({
            "x1": x1 / w, "y1": y1 / h,
            "x2": x2 / w, "y2": y2 / h,
            "confidence": conf
        })
    return detections

@app.post("/predict/")
async def predict(
    file: UploadFile = File(...),
    lat: float = Form(...),
    lon: float = Form(...),
    model_type: str = Form("tensorflow")
):
    contents = await file.read()

    if model_type == "yolo":
        detections = run_yolo(contents)
        pothole_detected = len(detections) > 0
        max_conf = max((d["confidence"] for d in detections), default=0.0)

        print(f"YOLO detections: {len(detections)}, max_conf: {max_conf}")
        print("Lat:", lat, "Lon:", lon)

        if pothole_detected:
            db.collection("potholes").add({
                "latitude": lat,
                "longitude": lon,
                "confidence": max_conf,
                "model": "yolo"
            })

        return {
            "model": "yolo",
            "pothole_detected": pothole_detected,
            "detections": detections
        }
    else:
        img = preprocess_tf(contents)
        prediction = float(tf_model.predict(img)[0][0])

        print("Prediccion TF:", prediction)
        print("Lat:", lat, "Lon:", lon)

        if prediction > 0.5:
            db.collection("potholes").add({
                "latitude": lat,
                "longitude": lon,
                "confidence": prediction,
                "model": "tensorflow"
            })

        return {"model": "tensorflow", "prediction": prediction}

@app.get("/potholes")
def get_potholes():
    docs = db.collection("potholes").stream()
    potholes = []
    for doc in docs:
        potholes.append(doc.to_dict())
    return potholes
