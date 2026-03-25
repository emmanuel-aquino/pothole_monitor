document.getElementById("camera").addEventListener("change", function () {
    const file = this.files[0];
    document.getElementById("status").innerText = "Obteniendo ubicación GPS...";
    navigator.geolocation.getCurrentPosition(position => {
	const formData = new FormData();
	formData.append("file", file);
	formData.append("lat", position.coords.latitude);
	formData.append("lon", position.coords.longitude);
	document.getElementById("status").innerText = "Analizando imagen con IA...";
	fetch("http://127.0.0.1:8000/predict/", {
	    method: "POST",
	    body: formData
	})
		.then(res => res.json())
		.then(data => {
		    let prob = (data.prediction * 100).toFixed(2);
		    if (data.prediction > 0.5) {
			document.getElementById("result").innerHTML = "⚠️ Bache detectado (" + prob + "%)";
		    } else {
			document.getElementById("result").innerHTML = "✅ Camino normal (" + prob + "%)";
		    }
		    document.getElementById("status").innerText = "Proceso finalizado";
		});
    });
});