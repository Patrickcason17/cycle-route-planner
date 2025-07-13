let map = L.map('map', { zoomControl:false }).setView([13.0827,80.2707],13);
L.control.zoom({position:'bottomright'}).addTo(map);
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png').addTo(map);

let routeLayer, poiLayer = L.layerGroup().addTo(map);

async function showRoute() {
  document.getElementById('loading').classList.remove('hidden');
  const start = document.getElementById('start').value;
  const end = document.getElementById('end').value;
  const stops = document.getElementById('stops').value.split('\n').filter(s=>s);

  const res = await fetch('/route', {
    method:'POST',
    headers:{'Content-Type':'application/json'},
    body: JSON.stringify({start,end,stops})
  });
  const data = await res.json();
  document.getElementById('loading').classList.add('hidden');

  if(data.error) return alert(data.error);

  if(routeLayer) map.removeLayer(routeLayer);
  routeLayer = L.geoJSON(data.geojson).addTo(map);
  map.fitBounds(routeLayer.getBounds());

  L.marker(routeLayer.getBounds().getNorthWest(), {
    icon:L.icon({icon:'arrow-up',prefix:'fa'})
  });

  poiLayer.clearLayers();
  data.pois.forEach(p => {
    let icon = L.icon({
      iconUrl: p.type==='hotel'? 'https://img.icons8.com/color/48/000000/hotel.png' : 'https://img.icons8.com/color/48/000000/restaurant.png',
      iconSize:[32,32]
    });
    poiLayer.addLayer(L.marker([p.lat,p.lon],{icon}).bindPopup(`${p.type}: ${p.name}`));
  });

  document.getElementById('route-info').innerHTML = `<b>📍 Route Info</b><br>Distance: <b>${data.distance} km</b>`;
  document.getElementById('eta-info').innerHTML = `<b>⏱ ETA</b><br>Duration: ${data.duration} min<br>Start: ${data.start_time}<br>Arrival: ${data.arrival_time}`;
  document.getElementById('weather-info').innerHTML = `<b>🌤 Weather</b><br>${data.temp}°C, ${data.condition}<br>🔥 Calories: ${data.calories}`;
}
