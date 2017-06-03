"use strict";

var bdyNamesUrl = "../get-bdy-names";
var metadataUrl = "../get-metadata";
var dataUrl = "../get-data";

var map;
var info;
var themer;
var geojsonLayer;

var numClasses = 7; // number of classes (i.e colours) in map theme
var minZoom = 4;
var maxZoom = 16;
var currentZoomLevel;

var statsArray;
var currentStats;
var boundaryZooms;
var statsMetadata;
var boundaryOverride;

var currentBoundary;
var currentStatValues;
var currentStatDensities;
var currentStatNormalised;
var currentStatId;
var currentStatTable;
var currentStatType;
var currentStatDescription;

var currentStatClasses;
var colours = ['#fde0c5','#facba6','#f8b58b','#f59e72','#f2855d','#ef6a4c','#eb4a40']

// get querystring values
// code from http://forum.jquery.com/topic/getting-value-from-a-querystring
// get querystring as an array split on "&"
var querystring = location.search.replace('?', '').split('&');

// declare object
var queryObj = {};

// loop through each name-value pair and populate object
for (var i = 0; i < querystring.length; i++) {
    // get name and value
    var name = querystring[i].split('=')[0];
    var value = querystring[i].split('=')[1];
    // populate object
    queryObj[name] = value;
}

//// get/set values from querystring
//if (queryObj["census"] === undefined) {
//    census = "2016";
//} else {
//    census = queryObj["stats"];
//    // TODO: check census value is valid
//}

// get/set values from querystring

// auto-boundary override (for screenshots only! will create performance issues. e.g showing SA1's nationally!)
if (queryObj["b"] !== undefined) {
    boundaryOverride = queryObj["b"].toLowerCase();
}

// start zoom level
if (queryObj["z"] === undefined) {
    currentZoomLevel = 10;
} else {
    currentZoomLevel = queryObj["z"];
}

//// number of classes to theme the map - DOESN'T WORK YET
//if (queryObj["n"] === undefined) {
//    numClasses = 7;
//} else {
//    numClasses = queryObj["n"];
//}

// get the stat(s) - can include basic equations using + - * / and ()  e.g. B23 * (B45 + B678)
if (queryObj["stats"] === undefined) {
    statsArray = ["b3"]; // total_persons
} else {
    statsArray = encodeURIComponent(queryObj["stats"].toLowerCase()).split("%2C"); // handle maths operators as well as plain stats
//    console.log(statsArray);
}

function init() {
    //Initialize the map on the "map" div
    map = new L.Map('map', { preferCanvas: true });

    // acknowledge the data provider
    map.attributionControl.addAttribution('Census data &copy; <a href="http://www.abs.gov.au/websitedbs/d3310114.nsf/Home/Attributing+ABS+Material">ABS</a>');

    // load CARTO basemap tiles
    var tiles = L.tileLayer('http://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}.png', {
        attribution : '&copy; <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a> &copy; <a href="http://cartodb.com/attributions">CartoDB</a>',
        subdomains : 'abcd',
        minZoom : minZoom,
        maxZoom : maxZoom
    }).addTo(map);

    // set the view to a given center and zoom
    map.setView(new L.LatLng(-33.85, 151.15), currentZoomLevel);

    // get bookmarks
    var bmStorage = {
        getAllItems : function (callback) {
            $.getJSON('bookmarks.json',
                function (json) {
                    callback(json);
            });
        }
    };
    
    // add bookmark control to map
    var bmControl = new L.Control.Bookmarks({
        position : 'topleft',
        localStorage : false,
        storage : bmStorage
    }).addTo(map);

    // add control that shows info on mouseover
    info = L.control();
    info.onAdd = function (map) {
        this._div = L.DomUtil.create('div', 'info');
        this.update();
        return this._div;
    };
    info.update = function (props) {
//        var typePrefix;
//        var typeSuffix;
//        this._div.innerHTML = (props ? '<b>' + typePrefix + props[currentStatId].toLocaleString(['en-AU']) + typeSuffix + '</b> ' + currentStatType : 'pick a boundary');
        this._div.innerHTML = (props ? props.name + '<br/><b>' + props[currentStatId].toLocaleString(['en-AU']) + '</b> ' + currentStatType : 'pick a boundary');
    };
    info.addTo(map);

    // add radio buttons to choose mpa type: valume of stats, density (stat/area) or percent (normalised against B3 - total persons)
    var chooseMapType = L.control({
        position : 'bottomright'
    });
    chooseMapType.onAdd = function (map) {
        this._div = L.DomUtil.create('div', 'info themer');
        this._div.innerHTML = '<div><b>Map type </b>' +
                              '<input id="m1" type="radio" name="mapType" value="values" checked="checked"><label for="r1"><span><span></span></span>values</label> ' +
                              '<input id="m2" type="radio" name="mapType" value="density"><label for="r2"><span><span></span></span>density</label> ' +
                              '<input id="m3" type="radio" name="mapType" value="percent"><label for="r3"><span><span></span></span>percent</label>' +
                              '</div>';
        return this._div;
    };

    // event to trigger the map theme change
    $("input:radio[name=mapType]").click(function () {
        currentStatId = $(this).val();
        // update all stat metadata
        getCurrentStatMetadata();

//            // change styles for new stat - incompatible with current backend
//            geojsonLayer.eachLayer(function (layer) {
//                console.log(layer.feature);
//
//                layer.setStyle(style(layer.feature));
//            });

        // reload the data - NEEDS TO BE REPLACED WITH A MORE EFFICIENT WAY
        getData();
    });
    chooseMapType.addTo(map);
    // add radio buttons to choose stat to theme the map
    themer = L.control({
        position : 'bottomright'
    });
    themer.onAdd = function (map) {
        this._div = L.DomUtil.create('div', 'info themer');
        this.update();
        return this._div;
    };
    themer.update = function (radioButtons) {
        this._div.innerHTML = radioButtons;

        // event to trigger the map theme change
        $("input:radio[name=stat]").click(function () {
            currentStatId = $(this).val();
            // update all stat metadata
            getCurrentStatMetadata();

//            // change styles for new stat - incompatible with current backend
//            geojsonLayer.eachLayer(function (layer) {
//                console.log(layer.feature);
//
//                layer.setStyle(style(layer.feature));
//            });

            // reload the data - NEEDS TO BE REPLACED WITH A MORE EFFICIENT WAY
            getData();
        });
    };
    themer.addTo(map);

    // get a new set of data when map panned or zoomed
    // TODO: Handle map movement due to popup
    map.on('moveend', function (e) {
        getCurrentStatMetadata()
        getData();
    });

    // get list of boundaries and the zoom levels they display at
    // and get stats metadata, including map theme classes
    $.when(
        $.getJSON(bdyNamesUrl + "?min=" +  + minZoom.toString() + "&max=" + maxZoom.toString()),
        $.getJSON(metadataUrl + "?n=" +  + numClasses.toString() + "&stats=" + statsArray.join())
    ).done(function(bdysResponse, metadataResponse) {
        if (boundaryOverride === undefined){
            boundaryZooms = bdysResponse[0];
        } else {
            // create array of zoom levels with the override boundary id
            boundaryZooms = {}
            for (var j = minZoom; j <= maxZoom; j++) {
                boundaryZooms[j.toString()] = boundaryOverride;
            }
        }

        currentBoundary = boundaryZooms[currentZoomLevel.toString()];
        statsMetadata = metadataResponse[0].boundaries;

        // loop through each boundary to get the current one
        for (var i = 0; i < statsMetadata.length; i++) {
            if (statsMetadata[i].boundary === currentBoundary) {
                currentStats = statsMetadata[i].stats;
                currentStatId = currentStats[0].id.toLowerCase();
                currentStatTable = currentStats[0].table.toLowerCase();
                currentStatType = currentStats[0].type.toLowerCase();
                currentStatValues = currentStats[0].values;
                currentStatDensities = currentStats[0].densities;
                currentStatNormalised = currentStats[0].normalised;
                currentStatDescription = currentStats[0].description;
//                currentStat = currentStats[0]; // pick the first stat in the URL to map first
            }
        }

        // create the radio buttons
        setRadioButtons();

        // get the first lot of data
        getData();
    });
}

function setRadioButtons() {
    var radioButtons = '<h4>Active stat</h4>';

    for (var i = 0; i < currentStats.length; i++){
        var value = currentStats[i].id.toLowerCase();
        var description = currentStats[i].description;

        if (value == currentStatId) {
            radioButtons += '<div><input id="r' + i.toString() + '" type="radio" name="stat" value="' + value + '" checked="checked"><label for="r' + i.toString() + '"><span><span></span></span>' + description + '</label></div>';
        } else {
            radioButtons += '<div><input id="r' + i.toString() + '" type="radio" name="stat" value="' + value + '"><label for="r' + i.toString() + '"><span><span></span></span>' + description + '</label></div>';
        }
     }

    themer.update(radioButtons);
}

function getCurrentStatMetadata() {
    // get new zoom level and boundary
    currentZoomLevel = map.getZoom();
    currentBoundary = boundaryZooms[currentZoomLevel.toString()];

    // loop through each boundary to get the new sets of stats metadata
    for (var i = 0; i < statsMetadata.length; i++) {
        if (statsMetadata[i].boundary === currentBoundary) {
            currentStats = statsMetadata[i].stats;

            // loop through each stat to get the new classes
            for (var j = 0; j < currentStats.length; j++) {
                if (currentStats[j].id.toLowerCase() === currentStatId) {
                    currentStatTable = currentStats[j].table.toLowerCase();
                    currentStatType = currentStats[j].type.toLowerCase();
                    currentStatValues = currentStats[0].values;
                    currentStatDensities = currentStats[0].densities;
                    currentStatNormalised = currentStats[0].normalised;
                    currentStatDescription = currentStats[j].description;
                }
            }
        }
    }

//    console.log(currentStatClasses);
}

function getData() {

    console.time("got boundaries");

    //restrict to the zoom levels that have data
    if (currentZoomLevel < minZoom) {
        currentZoomLevel = minZoom;
    }
    if (currentZoomLevel > maxZoom) {
        currentZoomLevel = maxZoom;
    }

    // get map extents
    var bb = map.getBounds();
    var sw = bb.getSouthWest();
    var ne = bb.getNorthEast();

    // build URL
    var ua = [];
    ua.push(dataUrl);
    ua.push("?ml=");
    ua.push(sw.lng.toString());
    ua.push("&mb=");
    ua.push(sw.lat.toString());
    ua.push("&mr=");
    ua.push(ne.lng.toString());
    ua.push("&mt=");
    ua.push(ne.lat.toString());
    ua.push("&s=");
    ua.push(currentStatId);
    ua.push("&t=");
    ua.push(currentStatTable);
    ua.push("&b=");
    ua.push(currentBoundary);
    ua.push("&z=");
    ua.push((currentZoomLevel).toString());

    var requestString = ua.join('');

//    console.log(requestString);

    //Fire off AJAX request
    $.getJSON(requestString, gotData);
}

function gotData(json) {
    console.timeEnd("got boundaries");
    console.time("parsed GeoJSON");

    if (json !== null) {
        if(geojsonLayer !== undefined) {
            geojsonLayer.clearLayers();
        }

        geojsonLayer = L.geoJson(json, {
            style : style,
            onEachFeature : onEachFeature
        }).addTo(map);
    } else {
        alert("No data returned!")
    }

    console.timeEnd("parsed GeoJSON");
}

function style(feature) {
    var renderVal = parseInt(feature.properties[currentStatId]);

//    console.log(currentStatId);
//    console.log(renderVal);

    return {
        weight : 1.5,
        opacity : 0.2,
        color : '#fff',
        fillOpacity : 0.5,
        fillColor : getColor(renderVal)
    };
}

// get color depending on ratio of count versus max value
function getColor(d) {
    return  d > currentStatClasses[6] ? colours[6] :
            d > currentStatClasses[5] ? colours[5] :
            d > currentStatClasses[4] ? colours[4] :
            d > currentStatClasses[3] ? colours[3] :
            d > currentStatClasses[2] ? colours[2] :
            d > currentStatClasses[1] ? colours[1] :
                                        colours[0];
}

//// get color depending on ratio of count versus max value
//function getOpacity(d) {
//    return d > 500 ? 0.7 :
//        d > 250 ? 0.6 :
//        d > 100 ? 0.5 :
//        d > 50 ? 0.4 :
//        d > 25 ? 0.3 :
//        d > 0 ? 0.2 :
//                0.1;

function onEachFeature(feature, layer) {
    layer.on({
        mouseover : highlightFeature,
        mouseout : resetHighlight
//        onclick : zoomToFeature
    });
}

function highlightFeature(e) {
    var layer = e.target;

    // console.log(layer);

    layer.setStyle({
        weight : 2.5,
        opacity : 0.9,
        color : '#ffffff',
        fillOpacity : 0.7
    });

//    if (!L.Browser.ie && !L.Browser.edge && !L.Browser.opera) {
    layer.bringToFront();
//    }

    info.update(layer.feature.properties);
}

function resetHighlight(e) {
    geojsonLayer.resetStyle(e.target);
    info.update();
}

//function zoomToFeature(e) {
//    map.fitBounds(e.target.getBounds());
//}

// fix for Apple Magic Mouse jumpiness
var lastScroll = new Date().getTime();

L.Map.ScrollWheelZoom.prototype._onWheelScroll = function (e) {
  if (new Date().getTime() - lastScroll < 600) {
    e.preventDefault();
    return;
  }
  var delta = L.DomEvent.getWheelDelta(e);
  var debounce = this._map.options.wheelDebounceTime;

  if (delta >= -0.15 && delta <= 0.15) {
    e.preventDefault();
    return;
  }
  if (delta <= -0.25) delta = -0.25;
  if (delta >= 0.25) delta = 0.25;
  this._delta += delta;
  this._lastMousePos = this._map.mouseEventToContainerPoint(e);

  if (!this._startTime) {
      this._startTime = +new Date();
  }

  var left = Math.max(debounce - (+new Date() - this._startTime), 0);

  clearTimeout(this._timer);
  lastScroll = new Date().getTime();
  this._timer = setTimeout(L.bind(this._performZoom, this), left);

  L.DomEvent.stop(e);
}