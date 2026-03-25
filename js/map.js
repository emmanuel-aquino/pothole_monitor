
const map = L.map('map').setView([20.59, -100.39], 13);
const markerGroup = L.layerGroup().addTo(map); 

L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 19,
}).addTo(map);

function loadPotholes() {
    fetch("https://potholemonitor-production.up.railway.app/potholes")
        .then(res => {
            if (!res.ok) throw new Error("Error en la red");
            return res.json();
        })
        .then(data => {
            markerGroup.clearLayers();

            data.forEach(p => {
                const confidencePercent = (p.confidence * 100).toFixed(1);
                
                L.marker([p.latitude, p.longitude])
                    .addTo(markerGroup)
                    .bindPopup(`
                        <strong>Bache detectado</strong><br>
                        Confianza: ${confidencePercent}%
                    `);
            });
        })
        .catch(err => console.error("Error al cargar baches:", err));
}

// Carga inicial
loadPotholes();

// Refresco automático cada 5 segundos
setInterval(loadPotholes, 60000);