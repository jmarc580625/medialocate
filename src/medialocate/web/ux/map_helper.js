class MarkerManager {
  constructor(map) {
    this.logHelper = "MarkerManager: ";
    this.map = map;
    this.layerGroups = {};
    this.markers = {};
    this.idToGroup = {};
  }

  addMarker(key, latitude, longitude, group = "default") {
    console.debug(this.logHelper + 'add marker: ' + key + ' @ latitude: ' + latitude + ', longitude: ' + longitude + ', group: ' + group);
    if (! this.layerGroups.hasKey(group)) this.layerGroups[group] = L.layerGroup();
    var marker = L.marker([latitude, longitude]).addLayer(this.layerGroups[group]);
    marker.key = key;
    this.markers[group][key] =  marker;
    this.idToGroup[key] = group;
    marker.on('mouseover', function (e) {
      this._icon.classList.add("markerFocus");
      window.dispatchEvent(new CustomEvent(MARKER_FOCUS_EVENT, {detail: {id: key}}));
    }.bind(marker));
    marker.on('mouseout', function (e) {
      this._icon.classList.remove("markerFocus");
      window.dispatchEvent(new CustomEvent(MARKER_UNFOCUS_EVENT, {detail: {id: key}}));
    }.bind(marker));
  }

  hideGroup(group) {
    console.debug(this.logHelper + 'hide group: ' + group);
    this.map.removeLayer(this.layerGroups[group]);
  }

  showGroup(group) {
    console.debug(this.logHelper + 'hide group: ' + group);
    this.map.addLayer(this.layerGroups[group]);
  }

  deleteGroup(group = "default") {
    console.debug(this.logHelper + 'delete group: ' + group);
    if (! this.layerGroups.hasKey(group)) return;
    this.map.removeLayer(this.layerGroups[group]);
    layer = this.layerGroups[group];
    for (var key in this.markers[group]) {
      console.debug('removes marker : ' + key);
      layer.removeLayer(this.markers[group][key]);
    }
    delete this.markers[group];
    delete this.layerGroups[group];
  }

  focusToMarker(key) {
    console.debug(this.logHelper + 'focus to marker: ' + key);
    var pos = this.markers[key].getLatLng();
    this.map.panTo(pos);
    this.markers[key]._icon.classList.add("markerFocus");
    this.markers[key].setZIndexOffset(1000);
  }

  unfocusFromMarker(key) {
    console.debug(this.logHelper + 'unfocus from marker: ' + key);
    var pos = this.markers[key].getLatLng();
    this.markers[key]._icon.classList.remove("markerFocus");
    this.markers[key].setZIndexOffset(0);
  }
}

class MapHelper {

  constructor(container_id, center, zoom) {
    this.id = container_id;
    this.logHelper = "MapHelper: " + this.id + ': ';
    this.center = center;
    this.zoom = zoom;
    this.tileLayerURL = 'https://tile.openstreetmap.org/{z}/{x}/{y}.png';
    this.tileLayerAttribution = 'Map data &copy; <a href="http://openstreetmap.org">OpenStreetMap</a> contributors, <a href="http://creativecommons.org/licenses/by-sa/2.0/">CC-BY-SA</a>, Imagery Â© <a href="http://cloudmade.com">CloudMade</a>';
    this.map = null;
    this.markers = [];
    this.initialize();
  }

  initialize() {
    console.debug(this.logHelper + 'initialize');
    this.map = L.map(this.id);
    L.tileLayer(this.tileLayerURL, {
      maxZoom: 18,
      attribution: this.tileLayerAttribution
    }).addTo(this.map);
    this.map.setView([0.0, 0.0], 18);    // setView is needed before creating any marker, otherwise they did not get associated icon
  }

  setCenter() {
    console.debug(this.logHelper + 'set center @ latitude: ' + this.center.latitude + ', longitude: ' + this.center.longitude);
    var marker = L.marker([this.center.latitude, this.center.longitude]).addTo(this.map);
    marker._icon.classList.add("markerOrigin");
  }

  focusToCenter() {
    console.debug(this.logHelper + 'focus to center @ latitude: ' + this.center.latitude + ', longitude: ' + this.center.longitude + '& zoom: ' + this.zoom);
    this.map.setView(new L.LatLng(this.center.latitude, this.center.longitude), this.zoom);
  }

  addMarker(key, latitude, longitude) {
    console.debug(this.logHelper + 'add marker: ' + key + ' @ latitude: ' + latitude + ', longitude: ' + longitude + ', group: ' + group);
    var marker = L.marker([latitude, longitude]).addTo(this.map);
    marker.on('mouseover', function (e) {
      this._icon.classList.add("markerFocus");
      window.dispatchEvent(new CustomEvent(MEDIA_FOCUS_EVENT, {detail: {id: key}}));
    }.bind(marker));
    marker.on('mouseout', function (e) {
      this._icon.classList.remove("markerFocus");
      window.dispatchEvent(new CustomEvent(MEDIA_UNFOCUS_EVENT, {detail: {id: key}}));
    }.bind(marker));
    marker.key = key;
    this.markers[key] =  marker;
  }

  focusToMarker(key) {
    console.debug(this.logHelper + 'focus to marker: ' + key);
    var pos = this.markers[key].getLatLng();
    this.map.panTo(pos);
    this.markers[key]._icon.classList.add("markerFocus");
    this.markers[key].setZIndexOffset(1000);
  }

  unfocusFromMarker(key) {
    console.debug(this.logHelper + 'unfocus from marker: ' + key);
    var pos = this.markers[key].getLatLng();
    this.markers[key]._icon.classList.remove("markerFocus");
    this.markers[key].setZIndexOffset(0);
  }

  clear() {
    console.debug(this.logHelper + 'clear');
    for (var key in this.markers) {
      console.debug('removes marker : ' + key);
      this.map.removeLayer(this.markers[key]);
    }
  }
}


class MapHelper2 {

  constructor(container_id, center, zoom) {
    this.id = container_id;
    this.logHelper = "MapHelper: " + this.id + ': ';
    this.center = center;
    this.zoom = zoom;
    this.tileLayerURL = 'https://tile.openstreetmap.org/{z}/{x}/{y}.png';
    this.tileLayerAttribution = 'Map data &copy; <a href="http://openstreetmap.org">OpenStreetMap</a> contributors, <a href="http://creativecommons.org/licenses/by-sa/2.0/">CC-BY-SA</a>, Imagery Â© <a href="http://cloudmade.com">CloudMade</a>';
    this.map = this.initializeMap();
    this.markers = MarkerManager(this.map);
  }

  initializeMap() {
    console.debug(this.logHelper + 'initialize');
    map = L.map(this.id);
    L.tileLayer(this.tileLayerURL, {
      maxZoom: 18,
      attribution: this.tileLayerAttribution
    }).addTo(map);
    map.setView([0.0, 0.0], 18);    // setView is needed before creating any marker, otherwise they did not get associated icon
    return map
  }

  setCenter() {
    console.debug(this.logHelper + 'set center @ latitude: ' + this.center.latitude + ', longitude: ' + this.center.longitude);
    var marker = L.marker([this.center.latitude, this.center.longitude]).addTo(this.map);
    marker._icon.classList.add("markerOrigin");
  }

  focusToCenter() {
    console.debug(this.logHelper + 'focus to center @ latitude: ' + this.center.latitude + ', longitude: ' + this.center.longitude + '& zoom: ' + this.zoom);
    this.map.setView(new L.LatLng(this.center.latitude, this.center.longitude), this.zoom);
  }

  addMarker(key, latitude, longitude) {
    this.markers.addMarker(key, latitude, longitude);
  }

  showGroup(group) {
    this.markers.showGroup(group);
  }

  hideGroup(group) {
    this.markers.hideGroup(group);
  }

  focusToMarker(key) {
    this.markers.focusToMarker(key);
  }

  unfocusFromMarker(key) {
    this.markers.unfocusFromMarker(key);
  }

  clear(group = "default") {
    this.markers.deleteGroup(group);
  }
}
