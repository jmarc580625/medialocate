// utility function
function findAncestor (el, cls) {
  while ((el = el.parentNode) && el.className.indexOf(cls) < 0);
  return el;
} 

class MediaHelper {
  constructor(conteneur_id, template_id, gps_reference = {latitude: 0, longitude: 0}, bearing_range = 30) {
    this.id = conteneur_id;
    this.logHeader = "MediaHelper: " + this.id + ": ";
    this.conteneur = document.getElementById(conteneur_id);
    this.template = document.getElementById(template_id);
    this.gps_reference = gps_reference;
    this.bearing_range = bearing_range;

    this.conteneur.addEventListener('scroll', this._loadImagesLazily);
    this.conteneur.addEventListener('resize', this._loadImagesLazily);
  }

  add(location_data, path_to_data = '') {
      console.debug(this.logHeader + "add");
      this._addContent(this._sort(location_data), path_to_data);
      this._loadImagesLazily();
  }

  /*
  _sort recieves media description structures, and sort them according to their gps location.

  parameters:
  - locationData : a dictionnary of media descriptions holding gps location data
  - gpsReference : a gps location structure {latitude, longitude} used as a reference point to sort media descriptions
  - bearingRange : a integer value in the range [1..360] and divider of 360 used to group gps locations bearing within the sort algorithm

  input media description must adhere to the below json syntax and convention:
  - <id> :  a unique key
  - mediasource :  an url toward the media (video or picture)
  - mediathumbnail :  an url toward a picture thumbnail representing the media
  - mediatype : a word describing the type of media (video, picture, etc.)
  - mediaformat : a word describing the media format (jpg, mp4, mp3, etc.)
  - latitude : the latitude associated with the media
  - longitude : the longitude associated with the media
  output media description follows the example at the right below.

                                                                            | {
  "<id>": {                                                                 |   "id":"15accc49d53cfe17951d2a88cb183d76",
    "mediasource":"./Alaska-Brown-Bears-03.mp4",                            |   "mediasource":"./Alaska-Brown-Bears-03.mp4",
    "mediathumbnail":"./.mediaLocate/15accc49d53cfe17951d2a88cb183d76.jpg", |   "mediathumbnail":"./.mediaLocate/15accc49d53cfe17951d2a88cb183d76.jpg",
    "mediatype":"video",                                                    |   "mediatype":"video",
    "mediaformat":"mp4",                                                    |   "mediaformat":"mp4",
    "gps":{                                                                 |   "gps":{
      "latitude":"64.9500578383333",                                        |     "latitude":"64.9500578383333",
      "longitude":"-149.333549994667"                                       |     "longitude":"-149.333549994667"
    }                                                                       |   }
  }                                                                         |   "distance": 0.0,
                                                                            |   "bearing": 0.0
                                                                            | }

  The sort algorithm relies on both the bearing angle and the distance from the gps reference point toward the media gps location.
  */
  _sort (media_data) {
    console.debug(this.logHeader + " sort content");
    var media_descriptions =[];
    const entries = Object.entries(media_data);
    for (let key in media_data) {
      console.debug(this.logHeader + key + ': ' + media_data[key].mediasource);
      var value = media_data[key];
      try {
        value.distance = getDistance(this.gps_reference, value.gps.latitude, value.gps.longitude);
        value.bearing = getBearing(this.gps_reference, value.gps.latitude, value.gps.longitude);
        value.id = key;
        media_descriptions.push(value);
      } catch(err) {
        console.error('data element ignored: '+ err.message);
      }
    }
    return media_descriptions.sort(function sortPosition(pos1, pos2) {
      if (Math.floor(pos1.bearing / this.bearing_range) > Math.floor(pos2.bearing / this.bearing_range)) return -1;
      if (Math.floor(pos1.bearing / this.bearing_range) < Math.floor(pos2.bearing / this.bearing_range)) return 1;
      return (pos1.distance > pos2.distance ? 1 : -1)
    }.bind(this)); 
  } 

  /*
  addContent generates html elements based on media descriptions and html template and add those generates html elements
  within a given html container element.

  parameters:
  - conteneur : a html element which can contain childs elements and will receive generated elements
  - template : an html template element used to generate html elements
  - mediaDescription : an array of media description structure (see _sort) holding data used to generate new html elements 

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
  _addContent(media_descriptions, path_to_data) {
    console.debug(this.logHeader + " add content, " + 'path_to_data: ' + path_to_data);
    if (path_to_data !== '') {
      path_to_data = path_to_data + '/';
    }
    for (var i = 0; i < media_descriptions.length; i++) {
      var latitude = media_descriptions[i].gps.latitude;
      var longitude = media_descriptions[i].gps.longitude;

      var clone = this.template.content.cloneNode(true);

      var parent = clone.querySelector('.parent');
      parent.setAttribute("id", media_descriptions[i].id);
      parent.setAttribute("data-latitude", latitude);
      parent.setAttribute("data-longitude", longitude);

      var media = clone.querySelector('.media');
      media.setAttribute("href", path_to_data + media_descriptions[i].mediasource);

      var child = clone.querySelector('.child');
      child.setAttribute("data-src", path_to_data + media_descriptions[i].mediathumbnail);
      console.debug(this.logHeader + 'thumbnail: ' + path_to_data + media_descriptions[i].mediathumbnail);

      var oms = clone.querySelector('.oms');
      oms.setAttribute("href", `https://nominatim.openstreetmap.org/ui/reverse.html?lat=${latitude}&lon=${longitude}&zoom=18`);

      var maps  = clone.querySelector('.maps');
      maps.setAttribute("href", `https://www.google.fr/maps?&q=${latitude},${longitude}&z=17`);
          
      const myPromise = new Promise ((resolve, reject) => {
        this.conteneur.appendChild(clone);
        resolve(parent);
      });
      myPromise.then((value) => { 
        this._initializeEventHandlers(value);
      })
      .catch((err) => { console.error(err); });
    }
  }

  _initializeEventHandlers(element) {

    var latitude = element.getAttribute("data-latitude");
    var longitude = element.getAttribute("data-longitude");
    var key = element.getAttribute("id");
  
    window.dispatchEvent(new CustomEvent(MARKER_ADD_EVENT, {detail: {id: key, latitude: latitude, longitude: longitude}}));
  
    var child = element.getElementsByClassName('child')[0]
  
    child.addEventListener('mouseover', function (event) {
      var key = findAncestor(event.target, "parent").getAttribute("id");
      window.dispatchEvent(new CustomEvent(MARKER_FOCUS_EVENT, {detail: {id: key}}));
    });
  
    child.addEventListener('mouseout', function (event) {
      var key = findAncestor(event.target, "parent").getAttribute("id");
      window.dispatchEvent(new CustomEvent(MARKER_UNFOCUS_EVENT, {detail: {id: key}}));
    });
  } 

  clear() {
    console.debug(this.logHeader + "clear");
    this.conteneur.replaceChildren();
  }

  focusToMedia(key) {
    console.debug(this.logHeader + "focus to media: " + key);
    var element = document.getElementById(key);
    element.classList.add("mediaFocus");
    element.scrollIntoView({ behavior: "smooth", block: "nearest" });
  } 

  unfocusFromMedia(key) {
    console.debug(this.logHeader + "unfocus from media: " + key);
    var element = document.getElementById(key);
    element.classList.remove("mediaFocus");
  }

  _loadImagesLazily() {
    var images = document.querySelectorAll("img[data-src]");
    console.debug(this.logHeader + 'remaining lazy load: '+ images.length);
    for (let i = 0; i < images.length; i++) {
        let rect = images[i].getBoundingClientRect();
        if (images[i].hasAttribute("data-src")
        && rect.bottom > 0 && rect.top < window.innerHeight
        && rect.right > 0 && rect.left < window.innerWidth) {
            images[i].setAttribute("src", images[i].getAttribute("data-src"));
            images[i].removeAttribute("data-src");
        }
    }
  };
}
