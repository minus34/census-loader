"use strict";

var bdyNamesUrl = "../get-bdy-names";
var metadataUrl = "../get-metadata";
var dataUrl = "../get-data";

var map;
var info;
// var legend;
var themer;
var geojsonLayer;

var numClasses = 7; // number of classes (i.e colours) in map theme
var minZoom = 4;
var maxZoom = 16;
var currentZoomLevel = 0;
var censusYear = "";

var statsArray = [];
var currentStat;
var currMapMin = 0;
var currMapMax = 0;
var boundaryZooms;
var currentStats;
var boundaryOverride = "";

var currentBoundary = "";
var currentBoundaryMin = 7;
var currentStatId = "";

var highlightColour = "#ffff00";
var lowPopColour = "#422";
var colourRamp;
var colourRange = ["#1f1f1f", "#e45427"]; // dark grey > orange/red
//var colourRange = ["#1a1a1a", "#DD4132"]; // dark grey > red
//var colourRange = ["#1a1a1a", "#92B558"]; // dark grey > green

// get querystring values
// code from http://forum.jquery.com/topic/getting-value-from-a-querystring
// get querystring as an array split on "&"
var querystring = location.search.replace("?", "").split("&");

// declare object
var queryObj = {};

// loop through each name-value pair and populate object
var i;
for (i = 0; i < querystring.length; i+=1) {
    // get name and value
    queryObj[querystring[i].split("=")[0]] = querystring[i].split("=")[1];
}

// get/set values from querystring
if (!queryObj.census) {
   censusYear = "2016";
} else {
   censusYear = queryObj.census;
   // TODO: CHECK CENSUS YEAR VALUE IS VALID (2011 OR 2016 ONLY)
}

// get/set values from querystring

// auto-boundary override (for screenshots only! will create performance issues. e.g showing SA1"s nationally!)
if (queryObj.b !== undefined) {
    boundaryOverride = queryObj.b.toLowerCase();
}

// start zoom level
if (!queryObj.z) {
    currentZoomLevel = 11;
} else {
    currentZoomLevel = queryObj.z;
}

//// number of classes to theme the map - TODO: ADD SUPPORT FOR CUSTOM NUMBER OF MAP CLASSES
//if (!queryObj["n"]) {
//    numClasses = 7;
//} else {
//    numClasses = queryObj["n"];
//}

// get the stat(s) - can include basic equations using + - * / and ()  e.g. B23 * (B45 + B678)
if (!queryObj.stats) {
    if (censusYear === "2016") {
        statsArray = ["g3", "g1", "g2"]; // total_persons
    } else {  // 2011
        statsArray = ["b3", "b1", "b2"]; // total_persons
    }
} else {
    statsArray = encodeURIComponent(queryObj.stats.toLowerCase()).split("%2C");
    // TODO: handle maths operators as well as plain stats
}

function init() {
    // initial stat is the first one in the querystring
    currentStatId = statsArray[0];

    // create colour ramp
    colourRamp = new Rainbow();
    colourRamp.setSpectrum(colourRange[0], colourRange[1]);

    //Initialize the map on the "map" div - only use canvas if supported (can be slow on Safari)
    var elem = document.createElement("canvas");
    if (elem.getContext && elem.getContext("2d")) {
        map = new L.Map("map", { preferCanvas: true });
    } else {
        map = new L.Map("map", { preferCanvas: false });
    }

    // map = new L.Map("map", { preferCanvas: false }); // canvas slows Safari down versus Chrome (IE & edge are untested)

    // acknowledge the data provider
    map.attributionControl.addAttribution("Census data &copy; <a href='http://www.abs.gov.au/websitedbs/d3310114.nsf/Home/Attributing+ABS+Material'>ABS</a>");

    // create non-interactive pane (i.e. no mouse events) for basemap tiles
    map.createPane("basemap");
    map.getPane("basemap").style.zIndex = 650;
    map.getPane("basemap").style.pointerEvents = "none";

    // load CartoDB basemap
    L.tileLayer("http://cartodb-basemaps-{s}.global.ssl.fastly.net/dark_all/{z}/{x}/{y}.png", {
        attribution : "&copy; <a href='http://www.openstreetmap.org/copyright'>OpenStreetMap</a> &copy; <a href='http://cartodb.com/attributions'>CartoDB</a>",
        subdomains : "abcd",
        minZoom : minZoom,
        maxZoom : maxZoom,
        pane: "basemap",
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
        L.DomEvent.disableScrollPropagation(this._div);
        L.DomEvent.disableClickPropagation(this._div);
        this.update();
        return this._div;
    };
    info.update = function (props, colour) {
        var infoStr;

        if (props) {
            // improve the formatting of multi-name bdys
            var re = new RegExp(" - ", "g");
            var name = props.name.replace(re, "<br/>");

            infoStr = "<span style='font-weight: bold; font-size:1.5em'>" + name + "</span><br/>";

            // if no pop, nothing to display
            if (props.population === 0) {
                infoStr += "<span class='highlight' style='background:" + lowPopColour + "'>no population</span>";
            } else {
                // // special case if value is total pop - convert to pop density
                // var stat = 0;
                // var type = "";
                // if (currentStat.description === "Total Persons Persons") {
                //     stat = props.density;
                //     type = "Persons / km<sup>2</sup>"
                // } else {
                //     stat = props[currentStatId]
                //     type = currentStat.type;
                // }

                var type = currentStat.type;
                var valStr = stringNumber(props[currentStatId], "values", type);
                var popStr = stringNumber(props.population, "values", "dummy") + " persons";


                if (currentStat.maptype === "values") {
                    var colour = getColor(props[currentStatId], 99999999); //dummy second value get's the right colour
                    infoStr += "<span class='highlight' style='background:" + colour + "'>" + type + ": " + valStr + "</span><br/>" + popStr;
                } else { // "percent"
                    var colour = getColor(props.percent, 99999999); //dummy second value get's the right colour
                    var percentStr = stringNumber(props.percent, "percent", type);
                    infoStr += "<span class='highlight' style='background:" + colour + "'>" + currentStat.description + ": " + percentStr + "</span><br/>" + valStr + " of " + popStr;
                }

                // highlight low population bdys
                if (props.population <= currentBoundaryMin) {
                    infoStr += "<br/><span class='highlight' style='background:" + lowPopColour + "'>low population</span>";
                }
            }
        } else {
            infoStr ="pick a boundary";
        }

        this._div.innerHTML = infoStr;
    };

    // add radio buttons to choose stat to theme the map
    themer = L.control({
        position : "bottomright"
    });

    themer.onAdd = function () {
        this._div = L.DomUtil.create("div", "info themer");
        L.DomEvent.disableScrollPropagation(this._div);
        L.DomEvent.disableClickPropagation(this._div);
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
        $.getJSON(bdyNamesUrl + "?min=" + minZoom.toString() + "&max=" + maxZoom.toString()),
        $.getJSON(metadataUrl + "?c="  + censusYear + "&n=" + numClasses.toString() + "&stats=" + statsArray.join())
    ).done(function(bdysResponse, metadataResponse) {
        if (!boundaryOverride){
            boundaryZooms = bdysResponse[0];
        } else {
            // create array of zoom levels with the override boundary id
            boundaryZooms = {};
            var j;
            for (j = minZoom; j <= maxZoom; j+=1) {
                boundaryZooms[j] = {
                    name: boundaryOverride,
                    min: currentBoundaryMin
                };
            }
        }

        // get the initial stat"s metadata
        currentStats = metadataResponse[0].stats;
        getCurrentStatMetadata();

        // show legend and info controls
        // legend.addTo(map);
        info.addTo(map);

        // get the first lot of data
        getData();
    });
}

function setRadioButtons() {
    // var radioButtons = "<h4>Active stat</h4>";
    var radioButtons = "";

    for (var i = 0; i < currentStats.length; i++){
        var value = currentStats[i].id;
        var description = currentStats[i].description;
        var type = currentStats[i].type;

        if (value === currentStatId) {
            //format values
            var mapType = currentStats[i].maptype;
            var minStr = stringNumber(currMapMin, mapType, type);
            var maxStr = stringNumber(currMapMax, mapType, type);

            radioButtons += "<div><input id='r" + i.toString() + "' type='radio' name='stat' value='" + value +
                "' checked='checked'><label for='r" + i.toString() + "'><span><span></span></span><b>" + description + "</b></label>" +
                "<div style='padding: 0.2em 0em 0.6em 1.8em'><table class='colours' ><tr><td>" + minStr + "</td><td style='width: 10em'></td><td>" + maxStr + "</td></tr></table></div></div>";
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

function stringNumber(val, mapType, type) {
    var numString = "";

    if (mapType === "values") {
        //add dollar sign
        if (type.indexOf("$/") !== -1) {
            numString = "$" + val.toLocaleString(["en-AU"]);
        } else {
            numString = val.toLocaleString(["en-AU"]);
        }
    } else { // i.e. "percent"
        //round percentages
        numString = val.toFixed(1).toLocaleString(["en-AU"]) + "%";
    }

    return numString;
}

function getData() {

    console.time("got boundaries");

    // get new zoom level and boundary
    currentZoomLevel = map.getZoom();
    currentBoundary = boundaryZooms[currentZoomLevel.toString()].name;
    currentBoundaryMin = boundaryZooms[currentZoomLevel.toString()].min;

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
    ua.push(censusYear);
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

        // get min and max values
        currMapMin = 999999999;
        currMapMax = -999999999;

        var features = json.features;

        for (var i = 0; i < features.length; i++){
            var props = features[i].properties;

            // only include if pop is significant
            if (props.population > currentBoundaryMin){
                var val = 0;

                if (currentStat.maptype === "values") {
                    val = props[currentStatId];
                } else { // "percent"
                    val = props.percent;
                }

                if (val < currMapMin) { currMapMin = val }
                if (val > currMapMax) { currMapMax = val }
            }
        }

        // correct max percents over 100% (where pop is less than stat, for whatever reason)
        if (currentStat.maptype === "percent" && currMapMax > 100.0) { currMapMax = 100.0 }

        // set the number range for the colour gradient (allow for decimals, convert to ints)
        var minInt = parseInt(currMapMin.toFixed(1).toString().replace(".",""));
        var maxInt = parseInt(currMapMax.toFixed(1).toString().replace(".",""));

        colourRamp.setNumberRange(minInt, maxInt);

        //update the legend with the new min and max
        // legend.update();

        // create the radio buttons
        setRadioButtons();

        // console.log(currMapMin);
        // console.log(currMapMax);

        // add data to map layer
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
        renderVal = props[currentStatId];
    } else {
        renderVal = props.percent;
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
function getColor(val, pop) {
    var colour = "";

    // show dark red/gray if low population (these can dominate the map)
    if (pop <= currentBoundaryMin){
        colour =  lowPopColour;
    } else {
        //convert value to int to get the right colour
        var valInt = parseInt(val.toFixed(1).toString().replace(".",""));
        colour = "#" + colourRamp.colourAt(valInt);
    }

    return colour;
}

function onEachFeature(feature, layer) {
    layer.on({
        mouseover : highlightFeature,
        mouseout : resetHighlight
        // click : zoomToFeature
    });
}

function highlightFeature(e) {
    var layer = e.target;

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

// function zoomToFeature(e) {
//    map.fitBounds(e.target.getBounds());
// }
