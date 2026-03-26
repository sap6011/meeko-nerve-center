async function fetchSolarWeather() {
    try {
        const response = await fetch('https://services.swpc.noaa.gov/products/summary/magnetic-field.json');
        const data = await response.json();
        const kpIndex = data.Kp || 3; // Default to 3 if unavailable
        const resonance = (kpIndex / 9) * 100;
        document.getElementById('res-val').innerText = `${resonance.toFixed(1)}% Solar Resonance`;
        document.getElementById('community-bar').style.width = `${resonance * 0.99}%`;
        document.getElementById('node-bar').style.width = `${resonance * 0.01}%`;
    } catch (e) {
        console.log("Storm interference. Using internal clock.");
    }
}
setInterval(fetchSolarWeather, 30000);
fetchSolarWeather();
