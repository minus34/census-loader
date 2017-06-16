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
var currentStat;
var boundaryZooms;
var currentStats;
var boundaryOverride;

var currentBoundary;
var currentStatId;

var highlightColour = "#ffff00"
var colours;
var percentColours = ["#1a1a1a", "#DD4132"];
//var percentColours = ["#1a1a1a", "#92B558"];

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
    // populate object
    queryObj[name] = querystring[i].split('=')[1];
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
    currentZoomLevel = 11;
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
    statsArray = ["b1", "b2"]; // total_persons

} else {
    statsArray = encodeURIComponent(queryObj["stats"].toLowerCase()).split("%2C");
    // TODO: handle maths operators as well as plain stats
}

function init() {

    // initial stat is the first one in the querystring
    currentStatId = statsArray[0]

    // create colour ramp
    colours = new Rainbow();
    colours.setNumberRange(1, numClasses);
    colours.setSpectrum(percentColours[0], percentColours[1]);

    //Initialize the map on the "map" div - only use canvas if supported
    var elem = document.createElement( "canvas" );

    if ( elem.getContext && elem.getContext( "2d" ) ) {
        map = new L.Map('map', { preferCanvas: true });
    } else {
       map = new L.Map('map', { preferCanvas: false });
    }

    // map = new L.Map('map', { preferCanvas: false }); // canvas slows Safari down versus Chrome (IE & edge are untested)

    // acknowledge the data provider
    map.attributionControl.addAttribution('Census data &copy; <a href="http://www.abs.gov.au/websitedbs/d3310114.nsf/Home/Attributing+ABS+Material">ABS</a>');

    // create pane for map labels - a non-interactive pane (i.e. no mouse events)
    map.createPane('labels');

    // This pane is above markers but below popups
    map.getPane('labels').style.zIndex = 650;

    // Layers in this pane are non-interactive and do not obscure mouse/touch events
    map.getPane('labels').style.pointerEvents = 'none';

    // load CartoDB labels
    L.tileLayer('http://cartodb-basemaps-{s}.global.ssl.fastly.net/dark_only_labels/{z}/{x}/{y}.png', {
        attribution : '&copy; <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a> &copy; <a href="http://cartodb.com/attributions">CartoDB</a>',
        subdomains : 'abcd',
        minZoom : minZoom,
        maxZoom : maxZoom,
        pane: 'labels'
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
    var bm = new L.Control.Bookmarks({
        position : 'topleft',
        localStorage : false,
        storage : bmStorage
    }).addTo(map);

    // add control that shows info on mouseover
    info = L.control();
    info.onAdd = function () {
        this._div = L.DomUtil.create('div', 'info');
        this.update();
        return this._div;
    };
    info.update = function (props) {
        this._div.innerHTML = (props ? '<h3>' + props.name + '</h3>' +
                                       props[currentStatId].toLocaleString(['en-AU']) + ' of ' + props.population.toLocaleString(['en-AU']) + ' ' + currentStat.type +
                                       '<h2>' + props.percent.toFixed(1).toLocaleString(['en-AU']) + '%</h2>' : 'pick a boundary');
    };
    info.addTo(map);

    // add radio buttons to choose stat to theme the map
    themer = L.control({
        position : 'bottomright'
    });

    themer.onAdd = function () {
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
    themer.update('<b>L O A D I N G . . .</b>');

    // get a new set of data when map panned or zoomed
    map.on('moveend', function () {
        getCurrentStatMetadata();
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
            boundaryZooms = {};
            for (var j = minZoom; j <= maxZoom; j++) {
                boundaryZooms[j.toString()] = boundaryOverride;
            }
        }

        // get the initial stat's metadata
        currentStats = metadataResponse[0].stats;
        getCurrentStatMetadata();

        // create the radio buttons
        setRadioButtons();

        // get the first lot of data
        getData();
    });
}

function setRadioButtons() {
    var radioButtons = '<h4>Active stat</h4>';

    for (var i = 0; i < currentStats.length; i++){
        var value = currentStats[i].id;
        var description = currentStats[i].description;

        if (value === currentStatId) {
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

    // loop through the stats to get the current one
    for (var i = 0; i < currentStats.length; i++) {
        if (currentStats[i].id === currentStatId) {
            currentStat = currentStats[i];
        }
    }
}

//// format a number for display based on the number of digits or decimal places
//function formatNumber(number) {
//    var s = number.toString();
//
//    var output;
//
//    if (s.indexOf('.') > 3) output = parseInt(s.split("."));
//    if (s.indexOf('.') > 1) output = parseInt(s.split("."));
//
//    while (s.length < s.indexOf('.') + 4) s += '0';
//
//    return output;
//}

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
    ua.push(currentStat.id);
    ua.push("&t=");
    ua.push(currentStat.table);
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
    var renderVal = parseInt(feature.properties.percent);

    return {
        weight : 2,
        opacity : 1.0,
        color : getColor(renderVal),
        fillOpacity : 1.0,
        fillColor : getColor(renderVal)
    };
}

// get color depending on ratio of count versus max value
function getColor(d) {
    var classes = currentStat[currentBoundary];

    var colour = d > classes[6] ? colours.colourAt(7) :
                 d > classes[5] ? colours.colourAt(6) :
                 d > classes[4] ? colours.colourAt(5) :
                 d > classes[3] ? colours.colourAt(4) :
                 d > classes[2] ? colours.colourAt(3) :
                 d > classes[1] ? colours.colourAt(2) :
                                             colours.colourAt(1);

    return "#" + colour;
}

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
        color : highlightColour
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

//// fix for Apple Magic Mouse jumpiness
//var lastScroll = new Date().getTime();
//L.Map.ScrollWheelZoom.prototype._onWheelScroll = function (e) {
//  if (new Date().getTime() - lastScroll < 600) {
//    e.preventDefault();
//    return;
//  }
//  var delta = L.DomEvent.getWheelDelta(e);
//  var debounce = this._map.options.wheelDebounceTime;
//
//  if (delta >= -0.15 && delta <= 0.15) {
//    e.preventDefault();
//    return;
//  }
//  if (delta <= -0.25) delta = -0.25;
//  if (delta >= 0.25) delta = 0.25;
//  this._delta += delta;
//  this._lastMousePos = this._map.mouseEventToContainerPoint(e);
//
//  if (!this._startTime) {
//      this._startTime = +new Date();
//  }
//
//  var left = Math.max(debounce - (+new Date() - this._startTime), 0);
//
//  clearTimeout(this._timer);
//  lastScroll = new Date().getTime();
//  this._timer = setTimeout(L.bind(this._performZoom, this), left);
//
//  L.DomEvent.stop(e);
//}