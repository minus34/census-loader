"use strict";

var restUrl = "../get-data";
var map;
var info;
var geojsonLayer;

var minZoom = 4;
var maxZoom = 16;
var zoomLevel = 10;

var census;
var stats;
var currentStat;
var currentStatType;

var colours = ['#f6d2a9','#f5b78e','#f19c7c','#ea8171','#dd686c','#ca5268','#b13f64']

// get querystring values

//Code from http://forum.jquery.com/topic/getting-value-from-a-querystring
// ***this goes on the global scope
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

// get/set values from querystring
if (queryObj["census"] === undefined) {
  census = "2016";
} else {
  census = queryObj["stats"];
  // TODO: check census value is valid
}
if (queryObj["stats"] === undefined) {
  statArray = ["B3"]; // total_persons
} else {
  statArray = queryObj["stats"].split(",");
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
	map.setView(new L.LatLng(-33.85, 151.15), zoomLevel);

    // add bookmark control to map
    // get bookmarks
	var storage = {
		getAllItems : function (callback) {
			$.getJSON('bookmarks.json',
				function (json) {
				callback(json);
			});
		}
	};
	var bmControl = new L.Control.Bookmarks({
        position : 'topleft',
        localStorage : false,
        storage : storage
    }).addTo(map);

	// add control that shows info on mouseover
	info = L.control();
	info.onAdd = function (map) {
		this._div = L.DomUtil.create('div', 'info');
		this.update();
		return this._div;
	};
	info.update = function (props) {
        this._div.innerHTML = (props ? '<b>$' + props.dollardiff.toLocaleString(['en-AU']) + '</b> difference' : 'pick a hex');
    };
    info.addTo(map);

    // add radio buttons to choose stat to theme the map
    var themer = L.control({
        position : 'bottomright'
    });
    themer.onAdd = function (map) {
        var div = L.DomUtil.create('div', 'info themer');
        div.innerHTML = '<h4>Profitability<br/>Metric</h4>' +
            '<div><input id="radio1" type="radio" name="radio" value="count"><label for="radio1"><span><span></span></span>Policies</label></div>' +
            '<div><input id="radio2" type="radio" name="radio" value="ratestrength" checked="checked"><label for="radio2"><span><span></span></span>Rate strength</label></div>' +
            '<div><input id="radio3" type="radio" name="radio" value="dollardiff"><label for="radio3"><span><span></span></span>$ Difference</label></div>'
        return div;
    };
    themer.addTo(map);

    // event to trigger the map theme to change
    $("input:radio[name=radio]").click(function () {
        valueType = $(this).val();
        //Reload the boundaries - NEEDS TO BE REPLACED WITH A MORE EFFICIENT WAY
        getBoundaries();
    });

    //Get a new set of boundaries when map panned or zoomed
    //TO DO: Handle map movement due to popup
    map.on('moveend', function (e) {
        // map.closePopup();
        getBoundaries();
    });

    // map.on('zoomend', function (e) {
    //     map.closePopup();
    //     //getBoundaries();
    // });

    //Get the first set of boundaries
    getBoundaries();
}

function getBoundaries() {

	console.time("got boundaries");

	// get zoom level
	zoomLevel = map.getZoom();
	//    console.log("Zoom level = " + zoomLevel.toString());

	//restrict to the zoom levels that have data
	if (zoomLevel < minZoom) {
		zoomLevel = minZoom;
	}
	if (zoomLevel > maxZoom) {
		zoomLevel = maxZoom;
    }

	// get map extents
	var bb = map.getBounds();
	var sw = bb.getSouthWest();
	var ne = bb.getNorthEast();

	// build URL with querystring
	var ua = [];
	ua.push(restUrl);
	ua.push("?ml=");
	ua.push(sw.lng.toString());
	ua.push("&mb=");
	ua.push(sw.lat.toString());
	ua.push("&mr=");
	ua.push(ne.lng.toString());
	ua.push("&mt=");
	ua.push(ne.lat.toString());
	ua.push("&z=");
	ua.push((zoomLevel).toString());
	//    ua.push("&t=");
	//    ua.push(valueType);

	var reqStr = ua.join('');

	//Fire off AJAX request
	$.getJSON(reqStr, loadBdysNew);
}

function loadBdysNew(json) {
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

	var renderVal;
	var colours;

	switch (valueType) {
	case "count":
		colours = countColours;
		renderVal = parseInt(feature.properties.count);
		break;
    case "dollardiff":
        colours = rateStrengthColours;
        renderVal = parseInt(feature.properties.dollardiff);
        break;
    case "ratestrength":
        colours = rateStrengthColours;
		renderVal = parseFloat(feature.properties.ratestrength);
		break;
	default:
		colours = rateStrengthColours;
		renderVal = parseFloat(feature.properties.ratestrength);
	}

	return {
		weight : 0,
		opacity : 0.0,
		color : '#666',
		fillOpacity : getOpacity(parseInt(feature.properties.count)),
		fillColor : getColor(renderVal, colours)
	};

    // fillOpacity : getOpacity(renderVal),

}

// get color depending on ratio of count versus max value
function getColor(d, colours) {

    var zoomDiff = 13 - zoomLevel;

    switch (valueType) {
        case "count":
            if (zoomDiff > 0) {
                d = d / Math.pow(4, zoomDiff);
            }

            return d > 500 ? colours[6] :
                d > 200 ? colours[5] :
                    d > 100 ? colours[4] :
                        d > 50 ? colours[3] :
                            d > 25 ? colours[2] :
                                d > 0 ? colours[1] :
                                    colours[0];
            break;

        case "dollardiff":
            // if (zoomDiff > 0) {
            //     d = d / Math.pow(4, zoomDiff);
            // }

            // var colour;
            //
            // if (d >= -25000 && d < -16000) {
            //     colour = colours[6]
            // } else if (d >= -16000 && d < -8000) {
            //     colour = colours[5]
            // } else if (d >= -8000 && d < 0) {
            //     colour = colours[4]
            // } else if (d = 0) {
            //     colour = colours[3]
            // } else if (d > 0 && d < 15000) {
            //     colour = colours[2]
            // } else if (d >= 12500 && d < 30000) {
            //     colour = colours[1]
            // } else {
            //     colour = colours[0]
            // }
            //
            // return colour;

            // 41226, "min": -24078
            //

            var values = dollarDiffMinMax[zoomLevel.toString()];

            return d > values[0] ? colours[6] :
                d > values[1] ? colours[5] :
                    d > values[2] ? colours[4] :
                        d > values[3] ? colours[3] :
                            d > values[4] ? colours[2] :
                                d > values[5] ? colours[1] :
                                    colours[0];
            break;

    case "ratestrength":
        return d > 1.7 ? colours[0] :
            d > 1.5 ? colours[1] :
            d > 1.3 ? colours[2] :
            d > 1.1 ? colours[3] :
            d > 0.9 ? colours[4] :
            d > 0.7 ? colours[5] :
                      colours[6];
        break;
	default:
        return d > 1.7 ? colours[0] :
            d > 1.5 ? colours[1] :
                d > 1.3 ? colours[2] :
                    d > 1.1 ? colours[3] :
                        d > 0.9 ? colours[4] :
                            d > 0.7 ? colours[5] :
                                colours[6];
	}
}

// get color depending on ratio of count versus max value
function getOpacity(d) {

	switch (valueType) {
	case "count":
		return d > 500 ? 0.7 :
		d > 250 ? 0.6 :
		d > 100 ? 0.5 :
		d > 50 ? 0.4 :
		d > 25 ? 0.3 :
		d > 0 ? 0.2 :
				0.1;
		break;
	// case "difference":
	//     zoomDiff = 11 - zoomLevel;
	//     if (zoomDiff > 0) {
	 //        d = d / Math.pow(4, zoomDiff)
	//     }
	//
	// 	return d > 500 ? 0.7 :
	// 	d > 200 ? 0.6 :
	// 	d > 100 ? 0.5 :
	// 	d > 50 ? 0.4 :
	// 	d > 25 ? 0.3 :
	// 	d > 0 ? 0.2 :
	// 	        0.1;
	// 	break;
	default:
		return d > 500 ? 0.7 :
		d > 200 ? 0.6 :
		d > 100 ? 0.5 :
		d > 50 ? 0.4 :
		d > 25 ? 0.3 :
		d > 0 ? 0.2 :
				0.1;
	}
}

function onEachFeature(feature, layer) {
	layer.on({
        mouseover : highlightFeature,
        mouseout : resetHighlight
	});
}

function highlightFeature(e) {
	var layer = e.target;

	// console.log(layer);

	layer.setStyle({
		weight : 2,
		opacity : 0.9,
		fillOpacity : 0.7
	});

	if (!L.Browser.ie && !L.Browser.opera) {
		layer.bringToFront();
	}

	info.update(layer.feature.properties);
}

function resetHighlight(e) {
	geojsonLayer.resetStyle(e.target);
	info.update();
}

// function zoomToFeature(e) {
// 	map.fitBounds(e.target.getBounds());
// }