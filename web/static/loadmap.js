"use strict";

var restUrl = "../get-data";
var map = null;
var info = null;
var geojsonLayer = null;
var minZoom = 4;
var maxZoom = 16;
var valueType = "ratestrength";
var zoomLevel = 10;

// // Rate Strength range of values (defines colour shading of hexes)
// var rateStrengthMid = 1.0; // profitable > 1.0, unprofitable < 1.0
// var rateStrengthMin = 0.5;
// var rateStrengthMax = 1.5;

var dollarDiffMinMax = [
    {"4": [154, 863, 3576, 16841, 95415, 678871, 112852135]},
    {"5": [203.5000000000000000, 997.5000000000000000, 3302.5000000000000000, 12936.5000000000000000, 59173.500000000000, 292804.500000000000, 58150302]},
    {"6": [190, 685, 2181, 7123, 22671, 123791, 47092373]},
    {"7": [126.0000000000000000, 476.5000000000000000, 1194.5000000000000000, 3018.0000000000000000, 8035.5000000000000000, 36037.000000000000, 15592257]},
    {"8": [103, 325, 696, 1424, 3386, 12955, 5403746]},
    {"9": [81, 243, 468, 873, 1857, 6581, 2185226]},
    {"10": [67.0000000000000000, 205.0000000000000000, 375.0000000000000000, 654.0000000000000000, 1306.0000000000000000, 4657.0000000000000000, 857963]},
    {"11": [54, 186, 332, 575, 1162, 4858, 276858]},
    {"12": [50, 183, 332, 598, 1324, 4531, 94984]},
    {"13": [42.0000000000000000, 184.0000000000000000, 343.0000000000000000, 615.0000000000000000, 1211.0000000000000000, 2730.0000000000000000, 41226]},
    {"14": [7, 147, 276, 457, 748, 1317, 29110]},
    {"15": [-33, 96, 190, 295, 448, 730, 29110]}

];

var countColours = ['#e4f1e1', '#b4d9cc', '#89c0b6', '#63a6a0', '#448c8a', '#287274', '#0d585f'];
// var rateStrengthColours = ['#d73027','#fc8d59','#fee08b','#ffffbf','#d9ef8b','#91cf60','#1a9850']; //diverging: red to yellow to green (Source: Colorbrewer)
var rateStrengthColours = ['#009392', '#39b185', '#9ccb86', '#e9e29c', '#eeb479', '#e88471', '#cf597e']; //diverging: red to yellow to green (Source: CARTO)

function init() {
	//Initialize the map on the "map" div
    map = new L.Map('map', { preferCanvas: true });


    // var tiles = L.tileLayer('https://ws.spookfish.com/api/WMTS/tile/1.0.0/MostRecent/GeneratedDefaultStyle/GoogleMapsCompatible/{z}/{x}/{y}.jpeg', {
    //     attribution : '&copy; <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a> &copy; <a href="http://cartodb.com/attributions">CartoDB</a>',
    //     subdomains : 'abcd',
    //     minZoom : minZoom,
    //     maxZoom : maxZoom
    // }).addTo(map);


    // load CartoDB basemap tiles
	var tiles = L.tileLayer('http://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}.png', {
			attribution : '&copy; <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a> &copy; <a href="http://cartodb.com/attributions">CartoDB</a>',
			subdomains : 'abcd',
			minZoom : minZoom,
			maxZoom : maxZoom
		}).addTo(map);

	//Set the view to a given center and zoom
	map.setView(new L.LatLng(-33.85, 151.15), zoomLevel);

	// Get bookmarks/
	var storage = {
		getAllItems : function (callback) {
			$.getJSON('bookmarks.json',
				function (json) {
				callback(json);
			});
		}
	};

	//Add bookmark control
	var bmControl = new L.Control.Bookmarks({
			position : 'topleft',
			localStorage : false,
			storage : storage
		}).addTo(map);

	//Acknowledge the PSMA Data
	map.attributionControl.addAttribution('Hex grid derived from <a href="http://data.gov.au/dataset/geocoded-national-address-file-g-naf">PSMA G-NAF</a>');

	// control that shows hex info on hover
	info = L.control();

	info.onAdd = function (map) {
		this._div = L.DomUtil.create('div', 'info');
		this.update();
		return this._div;
	};

	info.update = function (props) {
		switch (valueType) {
		case "count":
			this._div.innerHTML = (props ? '<b>' + props.count.toLocaleString(['en-AU']) + '</b> policies' : 'pick a hex');
			break;
        case "dollardiff":
            this._div.innerHTML = (props ? '<b>$' + props.dollardiff.toLocaleString(['en-AU']) + '</b> difference' : 'pick a hex');
            break;
        case "ratestrength":
			this._div.innerHTML = (props ? 'Rate strength: <b>' + props.ratestrength.toLocaleString(['en-AU']) + '</b><br/><b>' + props.count.toLocaleString(['en-AU']) + '</b> policies' : 'pick a hex');
			break;
		default:
            this._div.innerHTML = (props ? 'Rate strength: <b>' + props.ratestrength.toLocaleString(['en-AU']) + '</b>' : 'pick a hex');
        }
    };

    info.addTo(map);

    //Add radio buttons to choose map theme
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

    $("input:radio[name=radio]").click(function () {
        valueType = $(this).val();
        //Reload the boundaries
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

function onEachFeature(feature, layer) {
	layer.on({
        mouseover : highlightFeature,
        mouseout : resetHighlight
	});
}

function getBoundaries() {

	console.time("got boundaries");

	//Get zoom level
	zoomLevel = map.getZoom();
	//    console.log("Zoom level = " + zoomLevel.toString());

	//restrict to the zoom levels that have data
	if (zoomLevel < minZoom)
		zoomLevel = minZoom;
	if (zoomLevel > maxZoom)
		zoomLevel = maxZoom;

	//Get map extents
	var bb = map.getBounds();
	var sw = bb.getSouthWest();
	var ne = bb.getNorthEast();

	//Build URL with querystring - selects census bdy attributes, stats and the census boundary geometries as minimised GeoJSON objects
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
        // L.glify.shapes({
        //     map: map,
        //     click: function (feature, details) {
        //         //set up a standalone popup (use a popup as a layer)
        //         /*L.popup()
        //          .setLatLng(point)
        //          .setContent("You clicked the point at longitude:" + point.lng + ', latitude:' + point.lat)
        //          .openOn(map);*/
        //         console.log('hello');
        //     },
        //     data: json
        // });

        try {
			geojsonLayer.clearLayers();
		} catch (err) {
			//dummy
		}

		// TO FIX: ERRORS NOT BEING TRAPPED
		// try {
			geojsonLayer = L.geoJson(json, {
					style : style,
					onEachFeature : onEachFeature
				}).addTo(map);
		// } catch (err) {
		// 	alert("Couldn't get data!");
		// }
	}

	console.timeEnd("parsed GeoJSON");
}
