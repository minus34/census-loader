"use strict";

var bdyNamesUrl = "../get-bdy-names";
var metadataUrl = "../get-metadata";
var dataUrl = "../get-data";

var map;
var info;
var legend;
var themer;
var geojsonLayer;

var numClasses = 7; // number of classes (i.e colours) in map theme
var minZoom = 4;
var maxZoom = 16;
var currentZoomLevel = 0;

var statsArray = [];
var currentStat;
var boundaryZooms;
var currentStats;
var boundaryOverride = "";

var currentBoundary = "";
var currentBoundaryMin = 7;
var currentStatId = "";

var highlightColour = "#ffff00";
var colourRamp;
var colourRange = ["#1a1a1a", "#e45427"]; // dark grey > orange/red
//var colourRange = ["#1a1a1a", "#DD4132"]; // dark grey > red
//var colourRange = ["#1a1a1a", "#92B558"]; // dark grey > green

// get querystring values
// code from http://forum.jquery.com/topic/getting-value-from-a-querystring
// get querystring as an array split on "&"
var querystring = location.search.replace("?", "").split("&");

// declare object
var queryObj = {};

// loop through each name-value pair and populate object
for (var i = 0; i < querystring.length; i++) {
    // get name and value
    var name = querystring[i].split("=")[0];
    // populate object
    queryObj[name] = querystring[i].split("=")[1];
}

//// get/set values from querystring
//if (!queryObj["census"]) {
//    census = "2016";
//} else {
//    census = queryObj["stats"];
//    // TODO: CHECK CENSUS YEAR VALUE IS VALID (2011 OR 2016 ONLY)
//}

// get/set values from querystring

// auto-boundary override (for screenshots only! will create performance issues. e.g showing SA1"s nationally!)
if (queryObj["b"] !== undefined) {
    boundaryOverride = queryObj["b"].toLowerCase();
}

// start zoom level
if (!queryObj["z"]) {
    currentZoomLevel = 11;
} else {
    currentZoomLevel = queryObj["z"];
}

//// number of classes to theme the map - TODO: ADD SUPPORT FOR CUSTOM NUMBER OF MAP CLASSES
//if (!queryObj["n"]) {
//    numClasses = 7;
//} else {
//    numClasses = queryObj["n"];
//}

// get the stat(s) - can include basic equations using + - * / and ()  e.g. B23 * (B45 + B678)
if (!queryObj["stats"]) {
    statsArray = ["b3", "b1", "b2"]; // total_persons

} else {
    statsArray = encodeURIComponent(queryObj["stats"].toLowerCase()).split("%2C");
    // TODO: handle maths operators as well as plain stats
}

function init() {
    // initial stat is the first one in the querystring
    currentStatId = statsArray[0];

    // create colour ramp
    colourRamp = new Rainbow();
    colourRamp.setNumberRange(1, numClasses);
    colourRamp.setSpectrum(colourRange[0], colourRange[1]);

    //Initialize the map on the "map" div - only use canvas if supported
    var elem = document.createElement("canvas");

    if (elem.getContext && elem.getContext("2d")) {
        map = new L.Map("map", { preferCanvas: true });
    } else {
        map = new L.Map("map", { preferCanvas: false });
    }

    // map = new L.Map("map", { preferCanvas: false }); // canvas slows Safari down versus Chrome (IE & edge are untested)

    // acknowledge the data provider
    map.attributionControl.addAttribution("Census data &copy; <a href='http://www.abs.gov.au/websitedbs/d3310114.nsf/Home/Attributing+ABS+Material'>ABS</a>");

    // create pane for map labels - a non-interactive pane (i.e. no mouse events)
    // This pane is above markers but below popups
    // Layers in this pane are non-interactive and do not obscure mouse/touch events
    map.createPane("labels");
    map.getPane("labels").style.zIndex = 650;
    map.getPane("labels").style.pointerEvents = "none";

    // load CartoDB basemap
    L.tileLayer("http://cartodb-basemaps-{s}.global.ssl.fastly.net/dark_all/{z}/{x}/{y}.png", {
        attribution : "&copy; <a href='http://www.openstreetmap.org/copyright'>OpenStreetMap</a> &copy; <a href='http://cartodb.com/attributions'>CartoDB</a>",
        subdomains : "abcd",
        minZoom : minZoom,
        maxZoom : maxZoom,
        pane: "labels",
        opacity: 0.4
    }).addTo(map);

    // set the view to a given center and zoom
    map.setView(new L.LatLng(-33.85, 151.15), currentZoomLevel);

    // get bookmarks
    var bmStorage = {
        getAllItems : function (callback) {
            $.getJSON("bookmarks.json",
                function (json) {
                    callback(json);
            });
        }
    };

    // add bookmark control to map
    var bm = new L.Control.Bookmarks({
        position : "topleft",
        localStorage : false,
        storage : bmStorage
    }).addTo(map);

    // add control that shows info on mouseover
    info = L.control();
    info.onAdd = function () {
        this._div = L.DomUtil.create("div", "info");
        this.update();
        return this._div;
    };
    info.update = function (props) {
        var infoStr;

        if (props) {
            if (props.population === 0) {
                infoStr = "<h3>" + props.name + "</h3><span style='font-size: 1.1em; font-weight: bold'>no population";
            } else {
                if (currentStat.maptype === "values") {
                    infoStr = "<h3>" + props.name + "</h3>" +
                        "<span style='font-size: 1.1em; font-weight: bold'>" + currentStat.type + ": " + props[currentStatId].toLocaleString(["en-AU"]) + "</span><br/>" +
                        "Persons: " + props.population.toLocaleString(["en-AU"]);

                } else { // "percent"
                    infoStr = "<h3>" + props.name + "</h3>" +
                        "<span style='font-size: 1.1em; font-weight: bold'>" + currentStat.description + ": " + props.percent.toFixed(1).toLocaleString(["en-AU"]) + "%</span><br/>" +
                        props[currentStatId].toLocaleString(["en-AU"]) + " of " + props.population.toLocaleString(["en-AU"]) + " persons ";
                }
            }
        } else {
            infoStr ="pick a boundary"
        }

        this._div.innerHTML = infoStr;
    };

    //Create a legend control
    legend = L.control({ position: "topright" });
    legend.onAdd = function () {
        this._div = L.DomUtil.create("div", "legend");
        // this.update();
        return this._div;
    };
    legend.update = function () {
        var len = currentStat[currentBoundary].length,
            min = stringNumber(currentStat[currentBoundary][0]),
            max = stringNumber(currentStat[currentBoundary][len - 1]);

        this._div.innerHTML = "<div><table><tr><td>" + min + "</td><td class='colours' style='width: 15.0em'></td><td>" + max + "</td></tr></table></div>";
    };

    // add radio buttons to choose stat to theme the map
    themer = L.control({
        position : "bottomright"
    });

    themer.onAdd = function () {
        this._div = L.DomUtil.create("div", "info themer");
        this.update();
        return this._div;
    };

    themer.update = function (radioButtons) {
        this._div.innerHTML = radioButtons;

        // event to trigger the map theme change
        $("input:radio[name=stat]").click(function () {
            currentStatId = $(this).val();

            // update stat metadata and map data
            getCurrentStatMetadata();
            getData();
        });
    };
    themer.addTo(map);
    themer.update("<b>L O A D I N G . . .</b>");

    // get a new set of data when map panned or zoomed
    map.on("moveend", function () {
        getCurrentStatMetadata();
        getData();
    });

    // get list of boundaries and the zoom levels they display at
    // and get stats metadata, including map theme classes
    $.when(
        $.getJSON(bdyNamesUrl + "?min=" +  + minZoom.toString() + "&max=" + maxZoom.toString()),
        $.getJSON(metadataUrl + "?n=" +  + numClasses.toString() + "&stats=" + statsArray.join())
    ).done(function(bdysResponse, metadataResponse) {
        if (!boundaryOverride){
            boundaryZooms = bdysResponse[0];
        } else {
            // create array of zoom levels with the override boundary id
            boundaryZooms = {};
            for (var j = minZoom; j <= maxZoom; j++) {
                var boundary = {};
                boundary["name"] = boundaryOverride;
                boundary["min"] = currentBoundaryMin;
                boundaryZooms[j] = boundary;
            }
        }

        // get the initial stat"s metadata
        currentStats = metadataResponse[0].stats;
        getCurrentStatMetadata();

        // show legend and info controls
        legend.addTo(map);
        info.addTo(map);

        // get the first lot of data
        getData();

        // create the radio buttons
        setRadioButtons();
    });
}

function setRadioButtons() {
    var radioButtons = "<h4>Active stat</h4>";

    for (var i = 0; i < currentStats.length; i++){
        var value = currentStats[i].id;
        var description = currentStats[i].description;

        if (value === currentStatId) {
            radioButtons += "<div><input id='r" + i.toString() + "' type='radio' name='stat' value='" + value +
                "' checked='checked'><label for='r" + i.toString() + "'><span><span></span></span>" + description +
                "</label></div>";
        } else {
            radioButtons += "<div><input id='r" + i.toString() + "' type='radio' name='stat' value='" + value +
                "'><label for='r" + i.toString() + "'><span><span></span></span>" + description + "</label></div>";
        }
     }

    themer.update(radioButtons);
}

function getCurrentStatMetadata() {
    // loop through the stats to get the current one
    for (var i = 0; i < currentStats.length; i++) {
        if (currentStats[i].id === currentStatId) {
            currentStat = currentStats[i];
        }
    }
}

function stringNumber(val) {
    var numString = "";

    if (currentStat.maptype === "values") {
        // format number to nearest 100"s or 1000"s
        var len = val.toString().length - 2;

        if (len > 0) {
            var factor = Math.pow(10, len);
            numString = (Math.round(val / factor) * factor).toString();
        } else {
            numString = val.toString();
        }
    } else { // i.e. "percent"
        //round percentages
        numString = Math.round(val).toString() + "%";
    }

    return numString;
}

function getData() {

    console.time("got boundaries");

    // get new zoom level and boundary
    currentZoomLevel = map.getZoom();
    currentBoundary = boundaryZooms[currentZoomLevel.toString()].name;
    currentBoundaryMin = boundaryZooms[currentZoomLevel.toString()].min;

    //update the legend with the new stat min and max
    legend.update();

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
    ua.push("&m=");
    ua.push(currentStat.maptype);
    ua.push("&z=");
    ua.push((currentZoomLevel).toString());

    var requestString = ua.join("");

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
    var renderVal;
    var props = feature.properties;

    if (currentStat.maptype === "values") {
        renderVal = parseInt(props[currentStatId]);
    } else {
        renderVal = parseInt(props.percent);
    }

    var col = getColor(renderVal, props.population);

    return {
        weight : 2,
        opacity : 1.0,
        color : col,
        fillOpacity : 1.0,
        fillColor : col
    };
}

// get color depending on ratio of count versus max value
function getColor(d, pop) {
    var classes = currentStat[currentBoundary];

    // show generic gray if no population
    if (pop === 0){
        return "#422";
    } else {
        var colourNum = d > classes[6] ? 7 :
                        d > classes[5] ? 6 :
                        d > classes[4] ? 5 :
                        d > classes[3] ? 4 :
                        d > classes[2] ? 3 :
                        d > classes[1] ? 2 :
                                        1 ;

        // override if population is low and colour class is near to top (i.e. a small pop is distorting the map)
    //    if (pop <= currentBoundaryMin && colourNum > numClasses - 4) {
        if (pop <= currentBoundaryMin && colourNum > 3) {
            colourNum = colourNum - 3;
        }

        return "#" + colourRamp.colourAt(colourNum);
    }
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
        opacity : 0.8,
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
