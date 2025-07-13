from flask import Flask, render_template, request, jsonify
import requests
from datetime import datetime, timedelta

app = Flask(__name__)

ORS_API_KEY = 'eyJvcmciOiI1YjNjZTM1OTc4NTExMTAwMDFjZjYyNDgiLCJpZCI6IjJmNmUxZGM0ZjI3NTRhZTViMGJkZDczYjQ5M2RhMzM2IiwiaCI6Im11cm11cjY0In0='
OWM_API_KEY = '32e3b688272509d526d8d7d77c10a0d4'

def get_coordinates(place):
    url = f'https://nominatim.openstreetmap.org/search?q={place}&format=json'
    try:
        response = requests.get(url, headers={"User-Agent": "cycle-route-app"}).json()
        if response:
            return float(response[0]['lat']), float(response[0]['lon'])
    except:
        return None, None
    return None, None

def get_nearby_pois(lat, lon, radius=1000):
    overpass_url = 'https://overpass-api.de/api/interpreter'
    query = f'''
    [out:json];
    (
      node["amenity"="restaurant"](around:{radius},{lat},{lon});
      node["tourism"="hotel"](around:{radius},{lat},{lon});
    );
    out center;
    '''
    try:
        response = requests.get(overpass_url, params={'data': query}).json()
        pois = []
        for el in response.get('elements', []):
            name = el.get('tags', {}).get('name', 'Unnamed')
            typ = 'restaurant' if el['tags'].get('amenity') == 'restaurant' else 'hotel'
            pois.append({'lat': el['lat'], 'lon': el['lon'], 'name': name, 'type': typ})
        return pois
    except:
        return []

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/route', methods=['POST'])
def route():
    try:
        req = request.json
        start = req.get('start')
        end = req.get('end')
        stops = req.get('stops', [])

        coords = []
        for p in [start] + stops + [end]:
            lat, lon = get_coordinates(p)
            if lat is None:
                return jsonify({'error': f'Location not found: {p}'}), 400
            coords.append([lon, lat])

        ors_url = 'https://api.openrouteservice.org/v2/directions/cycling-regular/geojson'
        headers = {'Authorization': ORS_API_KEY}
        body = {"coordinates": coords}

        resp = requests.post(ors_url, json=body, headers=headers)
        route_data = resp.json()

        # Error handling for invalid ORS responses
        if 'features' not in route_data:
            return jsonify({'error': 'Route could not be generated. Check locations or reduce number of stops.'}), 400

        summary = route_data['features'][0]['properties']['summary']
        distance = round(summary['distance'] / 1000, 2)
        duration = round(summary['duration'] / 60, 2)
        calories = round(distance * 35)

        now = datetime.now()
        arrival = (now + timedelta(minutes=duration)).strftime('%I:%M %p')

        weather_url = f"https://api.openweathermap.org/data/2.5/weather?lat={coords[0][1]}&lon={coords[0][0]}&units=metric&appid={OWM_API_KEY}"
        weather = requests.get(weather_url).json()
        temp = weather['main']['temp']
        condition = weather['weather'][0]['description']

        pois = get_nearby_pois(coords[-1][1], coords[-1][0])

        return jsonify({
            'geojson': route_data,
            'distance': distance,
            'duration': duration,
            'calories': calories,
            'start_time': now.strftime('%I:%M %p'),
            'arrival_time': arrival,
            'temp': temp,
            'condition': condition,
            'pois': pois
        })

    except Exception as e:
        return jsonify({'error': f'Unexpected error: {str(e)}'}), 500

if __name__ == '__main__':
    app.run(debug=True)
