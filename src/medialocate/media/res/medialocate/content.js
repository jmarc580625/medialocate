/*
setContent retrieves media description from data tags, extracts media description from their value attribute 
and sort them according to their location. setContent returns an array of media description structures sorted
by gps location. 

parameters:
- locationData : a json  structure holding media files location data
- gpsReference : a gps location structure {latitude, longitude} holding a reference point used to sort media locations
- bearingRange : a integer value in the range [1..360] and divider of 360 used to group gps locations bearing within the sort algorithm

setContent retrieves data tags of the given class name in the curent html file.
Tag's value attribute holds the media description data adhering to the below json syntax and convention:
- <id> :  a unique key
- mediasource :  an url toward the media (video or picture)
- mediathumbnail :  an url toward a picture thumbnail representing the media
- mediatype : a word describing the type of media (video, picture, etc.)
- mediaformat : a word describing the media format (jpg, mp4, mp3, etc.)
- latitude : the latitude associated with the media
- longitude : the longitude associated with the media

"<id>": {
  "mediasource":"./Alaska-Brown-Bears-03.mp4",
  "mediathumbnail":"./.mediaLocate/15accc49d53cfe17951d2a88cb183d76.jpg",
  "mediatype":"video",
  "mediaformat":"mp4",
  "gps":{
    "latitude":"64.9500578383333",
    "longitude":"-149.333549994667"
  }
} 

The sort algorithm relies on both the bearing angle and the distance from the gps reference point toward the media gps location.
*/
  function setContent(locationData, gpsReference, bearingRange = 30) {
    var mediaDescriptions =[];
    const entries = Object.entries(locationData);
    for (let key in locationData) {
      console.log(key + ': ' + locationData[key].mediasource);
      var value = locationData[key];
      try {
        value.distance = getDistance(gpsReference,value.gps.latitude,value.gps.longitude);
        value.bearing = getBearing(gpsReference,value.gps.latitude,value.gps.longitude);
        value.id = key;
        mediaDescriptions.push(value);
      } catch(err) {
        console.log('data element ignored: '+ err.message);
      }
    }
  
    return mediaDescriptions.sort(function sortPosition(pos1, pos2) {
      if (Math.floor(pos1.bearing / bearingRange) > Math.floor(pos2.bearing / bearingRange)) return -1;
      if (Math.floor(pos1.bearing / bearingRange) < Math.floor(pos2.bearing / bearingRange)) return 1;
      return (pos1.distance > pos2.distance ? 1 : -1)
    }); 
} 

/*
addContent generates html elements based on media descriptions and html template and add those generates html elements
within a given html container element.

parameters:
- conteneur : a html element which can contain childs elements and will receive generated elements
- template : an html template element used to generate html elements
- mediaDescription : an array of media description structure (see setContent) holding data used to generate new html elements 

html generation is based on a template structure which is must comply with the following constraints:
- element with parent class holds in id             attribute a unique media key
- element with parent class holds in data-latitude  attribute the media gps latitude 
- element with parent class holds in data-longitude attribute the media gps longitude 
- element with media class  holds in href           attribute an url toward the media
- element with child class  holds in src            attribute an url toward the media thumbnail picture
- element with oms class    holds in href           attribute an url toward an openstreet map address search page based on media gps location
- element with maps class   holds in href           attribute an url toward an google map page based on media gps location

A template structure example is given below: 
 <template>
    <div class="parent container" id="">
    <a class="media" href="" target=_blank>
        <img class="child" src=""/>
    </a>
    <div class="locations">
        <a class="oms" href="" target=_blank></a>
        <a class="maps" href="" target=_blank></a>
    </div>
    </div>
</template>
*/
function addContent(conteneur, template, mediaDescriptions) {
  for (i = 0; i < mediaDescriptions.length; i++) {
    var latitude = mediaDescriptions[i].gps.latitude;
    var longitude = mediaDescriptions[i].gps.longitude;
    var clone = template.content.cloneNode(true);
    //console.log('clone: '+clone);
    parent = clone.querySelector('.parent');
    parent.setAttribute("id", mediaDescriptions[i].id);
    parent.setAttribute("data-latitude", latitude);
    parent.setAttribute("data-longitude", longitude);
    media = clone.querySelector('.media');
    media.setAttribute("href", mediaDescriptions[i].mediasource);
    child = clone.querySelector('.child');
    child.setAttribute("src", mediaDescriptions[i].mediathumbnail);
    console.log('thumbnail: ' + mediaDescriptions[i].mediathumbnail);
    oms = clone.querySelector('.oms');
    oms.setAttribute("href", `https://nominatim.openstreetmap.org/ui/reverse.html?lat=${latitude}&lon=${longitude}&zoom=18`);
    maps  = clone.querySelector('.maps');
    maps.setAttribute("href", `https://www.google.fr/maps?&q=${latitude},${longitude}&z=17`);
    //console.log('conteneur: '+JSON.stringify(conteneur));
        
    const myPromise = new Promise ((resolve, reject) => {
      conteneur.appendChild(clone);
      resolve(parent);
    });
    myPromise.then((value) => { 
      initializeEventHandlers(value);
    })
    .catch((err) => { console.error(err); });
  }
}

/*
initContent is a helper function which combines the setContent and addContent functions
parameters:
- conteneur : a html element which can contain childs elements and will receive generated elements
- template : an html template element used to generate html elements
- className : a class name used to retrieve the data elements within the curent html document
- gpsReference : a gps location structure {latitude, longitude} holding a reference point used to sort media locations
*/
function initializeContent(conteneur, template, locationData, gpsReference) {
    addContent(conteneur, template,  setContent(locationData, gpsReference));
}

//----------------------------------------------------------------------------------------------

function findAncestor (el, cls) {
  while ((el = el.parentNode) && el.className.indexOf(cls) < 0);
  return el;
} 


function inMarker(e) {   
  var element = document.getElementById(this.key);
  this._icon.classList.add("markerFocus");
  element.classList.add("mediaFocus");
  element.scrollIntoView({ behavior: "smooth", block: "nearest" });
} 

function outMarker(e) {   
  this._icon.classList.remove("markerFocus");
  var element = document.getElementById(this.key);
  element.classList.remove("mediaFocus");
}

//----------------------------------------------------------------------------------------------

function initializeEventHandlers(element) { 
    console.time('initializeEventHandlers');

    var latitude = element.getAttribute("data-latitude");
    var longitude = element.getAttribute("data-longitude");
    var key = element.getAttribute("id");
    var marker = L.marker([latitude, longitude]).addTo(map);
    marker.on('mouseover', inMarker);
    marker.on('mouseout', outMarker);
    marker.key = key;
    myMarkers[key] =  marker;

  var child = element.getElementsByClassName('child')[0]

  child.addEventListener('mouseover', function (event) {
    var element = findAncestor(event.target, "parent");
    var latitude = element.getAttribute("data-latitude");
    var longitude = element.getAttribute("data-longitude");
    var key = element.getAttribute("id");

    map.panTo(new L.LatLng(latitude, longitude));
    myMarkers[key]._icon.classList.add("markerFocus");
    myMarkers[key].setZIndexOffset(Math.floor(latitude)+10);
  })

  child.addEventListener('mouseout', function (event) {
    var element = findAncestor(event.target, "parent");
    var latitude = element.getAttribute("data-latitude");
    var key = element.getAttribute("id");

    myMarkers[key]._icon.classList.remove("markerFocus");
    myMarkers[key].setZIndexOffset(Math.floor(latitude)-10);
  })
  console.timeEnd('initializeEventHandlers');
} 
