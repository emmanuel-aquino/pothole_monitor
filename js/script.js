const toggle = document.getElementById("model-toggle");
const badge = document.getElementById("model-badge");
const labelTf = document.getElementById("model-label-tf");
const labelYolo = document.getElementById("model-label-yolo");

toggle.addEventListener("change", function () {
    if (this.checked) {
        badge.textContent = "Modelo activo: YOLO (Roboflow)";
        labelTf.classList.remove("active-label");
        labelYolo.classList.add("active-label");
    } else {
        badge.textContent = "Modelo activo: TensorFlow";
        labelTf.classList.add("active-label");
        labelYolo.classList.remove("active-label");
    }
    document.getElementById("result").innerHTML = "";
    document.getElementById("bbox-canvas").style.display = "none";
});

document.getElementById("camera").addEventListener("change", function () {
    const file = this.files[0];
    const modelType = toggle.checked ? "yolo" : "tensorflow";

    document.getElementById("status").innerText = "Obteniendo ubicación GPS...";

    navigator.geolocation.getCurrentPosition(position => {
        const formData = new FormData();
        formData.append("file", file);
        formData.append("lat", position.coords.latitude);
        formData.append("lon", position.coords.longitude);
        formData.append("model_type", modelType);

        document.getElementById("status").innerText = "Analizando imagen con IA...";

        fetch("https://potholemonitor-production.up.railway.app/predict/", {
            method: "POST",
            body: formData
        })
        .then(res => res.json())
        .then(data => {
            document.getElementById("status").innerText = "Proceso finalizado";

            if (data.model === "yolo") {
                handleYoloResult(data, file);
            } else {
                handleTfResult(data);
            }
        });
    });
});

function handleTfResult(data) {
    let prob = (data.prediction * 100).toFixed(2);
    if (data.prediction > 0.5) {
        document.getElementById("result").innerHTML = "⚠️ Bache detectado (" + prob + "%)";
    } else {
        document.getElementById("result").innerHTML = "✅ Camino normal (" + prob + "%)";
    }
    document.getElementById("bbox-canvas").style.display = "none";
}

function handleYoloResult(data, file) {
    const resultEl = document.getElementById("result");
    const canvas = document.getElementById("bbox-canvas");

    if (data.pothole_detected) {
        const count = data.detections.length;
        const maxConf = Math.max(...data.detections.map(d => d.confidence));
        resultEl.innerHTML = `⚠️ ${count} bache(s) detectado(s) (confianza máx: ${(maxConf * 100).toFixed(1)}%)`;
    } else {
        resultEl.innerHTML = "✅ Camino normal (YOLO: sin detecciones)";
    }

    // Draw bounding boxes on canvas
    const img = new Image();
    img.onload = function () {
        canvas.width = img.width;
        canvas.height = img.height;
        const ctx = canvas.getContext("2d");
        ctx.drawImage(img, 0, 0);

        ctx.strokeStyle = "#e74c3c";
        ctx.lineWidth = Math.max(2, img.width / 200);
        ctx.font = `${Math.max(14, img.width / 40)}px Arial`;
        ctx.fillStyle = "#e74c3c";

        data.detections.forEach(det => {
            const x = det.x1 * img.width;
            const y = det.y1 * img.height;
            const w = (det.x2 - det.x1) * img.width;
            const h = (det.y2 - det.y1) * img.height;
            ctx.strokeRect(x, y, w, h);
            ctx.fillText(`${(det.confidence * 100).toFixed(1)}%`, x + 4, y - 6);
        });

        canvas.style.display = "block";
    };
    img.src = URL.createObjectURL(file);
}
