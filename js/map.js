const map = L.map('map').setView([20.59, -100.39], 13);

L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 19,
}).addTo(map);

let clusterGroup = L.markerClusterGroup();
map.addLayer(clusterGroup);

function loadPotholes() {
    fetch("https://potholemonitor-production.up.railway.app/potholes")
        .then(res => {
            if (!res.ok) throw new Error("Error en la red");
            return res.json();
        })
        .then(data => {
            clusterGroup.clearLayers();

            data.forEach(p => {
                const confidencePercent = (p.confidence * 100).toFixed(1);
                const modelLabel = p.model === "yolo" ? "YOLO (Roboflow)" : "TensorFlow";

                L.marker([p.latitude, p.longitude])
                    .bindPopup(`
                        <strong>Bache detectado</strong><br>
                        Confianza: ${confidencePercent}%<br>
                        Modelo: ${modelLabel}
                    `)
                    .addTo(clusterGroup);
            });

            document.getElementById("counter").textContent =
                `Total de baches registrados: ${data.length}`;
        })
        .catch(err => console.error("Error al cargar baches:", err));
}

loadPotholes();
setInterval(loadPotholes, 60000);
