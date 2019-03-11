# -*- coding: utf-8 -*-


from flask import Flask
from flask import render_template
import random
import json
#import pandas as pd
from threading import Lock
from flask import  session, request
from flask_socketio import SocketIO, emit
import urllib.request

async_mode = None

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, async_mode=async_mode)
thread = None
thread_lock = Lock()

# =============================================================================
# Constants
# =============================================================================
UPDATE_INTERVAL=1 # seconds
SEND_POINTS=True
SEND_POLYGONS=True
SEND_LINES=True
TRACTS_PATH='data/tracts.geojson'
OVERPASS_AMENTITIES_ROOT='https://lz4.overpass-api.de/api/interpreter?data=[out:json][bbox];node[~"^(amenity|leisure|shop)$"~"."];out;&bbox='
OVERPASS_WAYS_ROOT='https://lz4.overpass-api.de/api/interpreter?data=[out:json][bbox];way;out;&bbox='
BOUNDS=-71.150273, 42.335509,  -71.008869, 42.399212
#W, S, E, N

GEOJSON_TEMPLATE={
    "type": "FeatureCollection",
    "crs": {
        "type": "name",
        "properties": {
            "name": "urn:ogc:def:crs:OGC:1.3:CRS84"
        }
    },
    "features": []
}

def background_thread():
    """send server generated events to clients."""
    count = 0
    while True:
        update={'data':{'spatial':{}, 'count':count, 'period': str(count)+':00'}}
        sample_ind=random.sample(range(len(points)),100)
        if SEND_POINTS==True:
            point_data=GEOJSON_TEMPLATE.copy()
            point_data['features']=[{'properties':{'scale': distances[i]/max_dist}, 
                                  'geometry':{"type":"Point", "coordinates":[points[i][0], points[i][1]]}}  for i in sample_ind]
            update['data']['spatial']['amenities']=point_data
        if SEND_LINES==True:
            line_data=GEOJSON_TEMPLATE.copy()
            line_data['features']=[{'properties':{'scale': distances[i]/max_dist}, 
                                      'geometry':{"type":"LineString", "coordinates":[[points[i][0], points[i][1]],[centre[0], centre[1]]]}}  for i in sample_ind] 
            update['data']['spatial']['to_centre']=line_data
        if SEND_POLYGONS==True:
            polygon_data=tracts.copy()
            polygon_data['features']=random.sample(polygon_data['features'], 10)
            update['data']['spatial']['tracts']=polygon_data
#        socketio.emit('backendUpdates',
#                      {'data': {'spatial':{'points':point_data, 'To Home':line_data}}, 'count': count, 'period': str(count)+':00'},
#                      namespace='/test')
        socketio.emit('backendUpdates',update, namespace='/test')
        socketio.sleep(UPDATE_INTERVAL)
        count+=1

@app.route('/')
def index():
    return render_template('index.html', async_mode=socketio.async_mode)


@socketio.on('my_event', namespace='/test')
def test_message(message):
    session['receive_count'] = session.get('receive_count', 0) + 1
    emit('my_response',
         {'data': 'return to sender '+message['data'], 'count': session['receive_count']})
    print('Recieved from front end: ' + str(message['data']))

@socketio.on('initialDataRequest', namespace='/test')
def initial_data(message):
    mapOptions={'style': 'mapbox://styles/mapbox/dark-v9', 'center': centre, 'pitch':0, 'zoom':13}
    emit('initialData', {'mapOptions': mapOptions,'data': { }})
    print('Recieved from front end: ' + str(message['data']))
    
@socketio.on('connect', namespace='/test')
def test_connect():
    global thread
    with thread_lock:
        if thread is None:
            thread = socketio.start_background_task(target=background_thread)
    emit('my_response', {'data': 'You are connected', 'count': 0})


@socketio.on('disconnect', namespace='/test')
def test_disconnect():
    print('Client disconnected', request.sid)

# =============================================================================
# Get SOme Data
# =============================================================================
tracts=json.load(open(TRACTS_PATH))
strBounds=str(BOUNDS[0])+','+str(BOUNDS[1])+','+str(BOUNDS[2])+','+str(BOUNDS[3])
amenities_url=OVERPASS_AMENTITIES_ROOT+strBounds
centre=[(BOUNDS[0]+BOUNDS[2])/2, (BOUNDS[1]+BOUNDS[3])/2]
with urllib.request.urlopen(amenities_url) as url:
    amenity_data=json.loads(url.read().decode())
#list of lon,lat
points=[[amenity_data['elements'][i]['lon'], amenity_data['elements'][i]['lat']] 
        for i in range(len(amenity_data['elements']))]
#list of distances from centre
#better to convert to Euclidean coordinates for this
distances=[(((ll[0]-centre[0])**2+(ll[1]-centre[1])**2)**(1/2))for ll in points]
max_dist=max(distances)


if __name__ == '__main__':
    socketio.run(app, debug=True)
    