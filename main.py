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
import onnxruntime as ort
import base64

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

# Load YOLO model (ONNX)
yolo_session = ort.InferenceSession("PotholeTestModel.onnx", providers=["CPUExecutionProvider"])
yolo_input_name = yolo_session.get_inputs()[0].name

# Firebase config
firebase_key = json.loads(os.environ["FIREBASE_KEY"])
cred = credentials.Certificate(firebase_key)
firebase_admin.initialize_app(cred)
db = firestore.client()

IMG_SIZE = 128
YOLO_SIZE = 640
CONF_THRESHOLD = 0.25
THUMB_WIDTH = 320
THUMB_HEIGHT = 240
THUMB_QUALITY = 60

def compress_image(image_bytes):
    npimg = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(npimg, cv2.IMREAD_COLOR)
    img = cv2.resize(img, (THUMB_WIDTH, THUMB_HEIGHT))
    _, buffer = cv2.imencode(".jpg", img, [cv2.IMWRITE_JPEG_QUALITY, THUMB_QUALITY])
    return base64.b64encode(buffer).decode("utf-8")

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
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    img_resized = cv2.resize(img_rgb, (YOLO_SIZE, YOLO_SIZE))
    img_input = np.transpose(img_resized, (2, 0, 1)).astype(np.float32) / 255.0
    img_input = np.expand_dims(img_input, axis=0)

    outputs = yolo_session.run(None, {yolo_input_name: img_input})

    # YOLOv8 ONNX output: [1, 4+num_classes, 8400]
    preds = outputs[0][0].T  # shape: [8400, 4+num_classes]

    detections = []
    for pred in preds:
        cx, cy, w, h = pred[0], pred[1], pred[2], pred[3]
        conf = float(np.max(pred[4:]))
        if conf >= CONF_THRESHOLD:
            x1 = float(max(0.0, (cx - w / 2) / YOLO_SIZE))
            y1 = float(max(0.0, (cy - h / 2) / YOLO_SIZE))
            x2 = float(min(1.0, (cx + w / 2) / YOLO_SIZE))
            y2 = float(min(1.0, (cy + h / 2) / YOLO_SIZE))
            detections.append({"x1": x1, "y1": y1, "x2": x2, "y2": y2, "confidence": conf})

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
                "model": "yolo",
                "image": compress_image(contents)
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
                "model": "tensorflow",
                "image": compress_image(contents)
            })

        return {"model": "tensorflow", "prediction": prediction}

@app.get("/potholes")
def get_potholes():
    docs = db.collection("potholes").stream()
    potholes = []
    for doc in docs:
        potholes.append(doc.to_dict())
    return potholes
