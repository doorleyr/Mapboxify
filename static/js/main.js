var Msg
var map
var myCustomControl
mapboxgl.accessToken = MAPBOX_TOKEN;

function initialMap(options){
  // Initialise the map  
  map = new mapboxgl.Map({
      container: 'map', // container id
      style: options.style,
      center: options.center, // starting position [lng, lat]
      zoom: options.zoom ,// starting zoom
      pitch: options.pitch
  }); 
}

$(document).ready(function(){ 

            /////////////////////////////////////////
            //Open the conections with the back end
            /////////////////////////////////////////

            // Use a "/test" namespace.
            namespace = '/test';
            // Connect to the Socket.IO server.
            var socket = io.connect(location.protocol + '//' + document.domain + ':' + location.port + namespace);
            // Event handler for new connections.
            socket.on('connect', function() {
              socket.emit('initialDataRequest', {data: 'Front end wants the initial data'});
              socket.emit('my_event', {data: 'Front end says: I\'m connected!'});
                
            });
            // Event handler for server replies.
            socket.on('my_response', function(msg) {           
                console.log(msg.data)
            });

            // Event handler for server sent data.
            socket.on('initialData', function(msg) {           
                console.log(msg.data);
                initialMap(msg.mapOptions);  
                // once the initoal data has been received, open a new handler for updates             
                map.on('load', function () {
                  socket.on('backendUpdates', function(msg) {           
                  console.log('Received an update');
                  makeMap(msg);
                  });

                });               
            });

            

});

function makeMap(thisMsg) {  
  data=thisMsg.data;
  period=thisMsg.period;

  for (var key in data.spatial) {
    if (typeof map.getSource(key) == "undefined"){
      console.log('Creating '+key+' for first time')
      map.addSource(key, { type: 'geojson', data: data.spatial[key] });
      console.log(data.spatial[key])
      if (data.spatial[key].features[0].geometry.type=='LineString'){
        map.addLayer({
              "id": key,
              "type": "line",
              "source": key,
              "layout": {
                "line-join": "round",
                "line-cap": "round"},
              "paint": {
                  "line-width":['+',1,['*', 2, ['get', 'scale']]],
                  "line-color":["case", 
                    ['>',['number',['get', 'scale']],0.8],['rgb', 200,0,0],
                    ['>',['number',['get', 'scale']],0.6],['rgb', 200,100,0],
                    ['>',['number',['get', 'scale']],0.4],['rgb', 200,200,0],
                    ['>',['number',['get', 'scale']],0.2],['rgb', 100,200,0],
                    ['rgb', 0,200,0]],
                  "line-opacity":1
              }    
          });
      }
      if (data.spatial[key].features[0].geometry.type=='Polygon'|data.spatial[key].features[0].geometry.type=='MultiPolygon'){
          map.addLayer({
                    "id": key,
                    "type": "fill",
                    "source": key,
                    'paint': {
                    'fill-color': '#fff',
                    'fill-opacity': 0.1
                  }           
          });
      }
      if (data.spatial[key].features[0].geometry.type=='Point'){
          map.addLayer({
                    "id": key,
                    "type": "circle",
                    "source": key,
                      'paint': {
                      'circle-color': ["case", 
                      ['>',['number',['get', 'scale']],0.8],['rgb', 200,0,0],
                      ['>',['number',['get', 'scale']],0.6],['rgb', 200,100,0],
                      ['>',['number',['get', 'scale']],0.4],['rgb', 200,200,0],
                      ['>',['number',['get', 'scale']],0.2],['rgb', 100,200,0],
                      ['rgb', 0,200,0]],
                      'circle-radius':5
                      }           
          });
      }
      ////////Toggle capability//////
      addToLayerControl(key);
      ////////Toggle capability//////
    }
    else{
      //update data only
      map.getSource(key).setData(data.spatial[key]); 
      console.log('updating '+key) 
    }
    
  }

}

  