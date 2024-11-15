/********** CONTROLER BASE CLASS **********/

class ActionController {
    constructor() {
        this.logHeader = "";
        this.elements = null;
        this.id = null;
    }

    _assertDivFound() {
        var result = true;
        for (var key in this.elements) {
            if (this.elements[key] == null) {
                console.debug(this.logHeader + key + " id not found");
                result = false;
            } else {
                console.debug(this.logHeader + key + " id found");
            }
        }
        return result;
    }
}    

/********** MENU CONTROLER **********/

/* menu resources */
const MENU_ID = "menu_bar";
const MENU_ITEM_CLOSE_ID = "menu_close";
const MENU_ITEM_EXIT_ID = "menu_exit";
const ALBUM_NAME_ID = "album_name";

class Menu extends ActionController {
    constructor() {
        super();
        this.id = MENU_ID;
        this.logHeader = "Menu: " + this.id + ": ";
        try {
            this.elements = {
                MENU_ID: document.getElementById(this.id),
                MENU_ITEM_CLOSE_ID: document.getElementById(MENU_ITEM_CLOSE_ID),
                MENU_ITEM_EXIT_ID: document.getElementById(MENU_ITEM_EXIT_ID),
                ALBUM_NAME_ID: document.getElementById(ALBUM_NAME_ID)
            };
            this.elements.MENU_ITEM_CLOSE_ID.onclick = function(event) {this.close();}.bind(this);
            this.elements.MENU_ITEM_EXIT_ID.onclick = function(event) {this.exit();}.bind(this);
            window.addEventListener(ALBUM_OPEN_EVENT, function(e) {
                console.debug(this.logHeader + 'receive message: ' + ALBUM_OPEN_EVENT + ' detail: ' + e.detail.id);
                this.elements.ALBUM_NAME_ID.innerHTML = e.detail.id;
            }.bind(this));
        } catch (e) {
            console.debug(this.logHeader + " constructor fail with error:" + e.message);
        }
    }

    close() {
        console.debug(this.logHeader + ' closing');
        this.elements.ALBUM_NAME_ID.innerHTML = ""
        window.dispatchEvent(new CustomEvent(ALBUM_CLOSE_EVENT));
    }
    
    exit() {
        console.debug(this.logHeader + ' exiting');
        if (confirm('Are you sure you want to exit?')) {
            const xmlhttp = new XMLHttpRequest();
            var menu = this;
            xmlhttp.onload = function() {
                console.debug(menu.logHeader + menu.id + ' exit acknowledged');
                var win = open(location, "_self");
                win.close();
            };
            xmlhttp.open('GET', SHUTDOWN_API);
            xmlhttp.send();
        }
    }
}

/********** ALBUM CHOOSER CONTROLER **********/

/* album chooser resources */
const ALBUM_CHOOSER_ID = "album_chooser";
const ALBUM_CHOOSER_LIST_ID = "album_chooser_list";
const ALBUM_CHOOSER_HEADER_ID = "album_chooser_header";
const ALBUM_CHOOSER_HEADER_INVITE = "please, choose an album!";

class AlbumChooser extends ActionController {
    constructor() {
        super();
        this.id = ALBUM_CHOOSER_ID;
        this.logHeader = "AlbumChooser: " + this.id + ": ";
        this.choose_header = "please, choose an album";
        this.list = null;
        try {
            this.elements = { 
                ALBUM_CHOOSER_ID : document.getElementById(this.id),
                ALBUM_CHOOSER_LIST_ID : document.getElementById(ALBUM_CHOOSER_LIST_ID),
                ALBUM_CHOOSER_HEADER_ID : document.getElementById(ALBUM_CHOOSER_HEADER_ID)//,
            };
            window.addEventListener(ALBUM_CLOSE_EVENT, function(e) {
                console.debug(this.logHeader + 'receive message: ' + ALBUM_CLOSE_EVENT);
                this.show();
            }.bind(this));
            window.addEventListener(ALBUM_OPEN_EVENT, function(e) {
                console.debug(this.logHeader + 'receive message: ' + ALBUM_OPEN_EVENT + ' detail: ' + e.detail.id);
                this.hide();
            }.bind(this));            
        } catch (e) {
            console.debug(this.logHeader + " constructor fail with error:" + e.message);
        }
    }
 
    get() {
        console.debug(this.logHeader + this.id + ' get albums');
        if (! this._assertDivFound()) return;
        const xmlhttp = new XMLHttpRequest();
        const album_chooser = this;
        xmlhttp.onload = function() {
            console.debug(album_chooser.logHeader + ' load albums');
            const myObj = JSON.parse(this.responseText);
            var list = document.createElement("ul");
            for (var key in myObj) {
                var item = document.createElement("li");
                var itemText = document.createTextNode(key);
                var itemLink = document.createElement("a");
                itemLink.href = "javascript:void(0)";
                itemLink.onclick = function(event) {
                    var source = event.target || event.srcElement;
                    var album = source.innerHTML;
                    console.debug(this.logHeader + "selected album: " + album);
                    window.dispatchEvent(new CustomEvent(ALBUM_OPEN_EVENT, {detail: {id: album}}));
                }.bind(album_chooser);
                itemLink.appendChild(itemText);
                item.appendChild(itemLink);
                list.appendChild(item);
            }
            album_chooser.elements.ALBUM_CHOOSER_ID.setAttribute("style", "background-image: none");
            album_chooser.list = list;
            album_chooser.elements.ALBUM_CHOOSER_LIST_ID.appendChild(album_chooser.list);
            album_chooser.elements.ALBUM_CHOOSER_HEADER_ID.innerText = album_chooser.choose_header;
        }
        xmlhttp.open('GET', LIST_ALBUMS_API);
        xmlhttp.send();
    }

    show() {
        console.debug(this.logHeader + "shown");
        if (! this._assertDivFound()) return;
        if (this.list == null) {
            this.get();
        }
        this.elements.ALBUM_CHOOSER_ID.style.visibility = "visible";
    }

    hide() {
        console.debug(this.logHeader + "hidden");
        if (! this._assertDivFound()) return;
        this.elements.ALBUM_CHOOSER_ID.style.visibility = "hidden";
    }
}

/********** MEDIA INFOS CONTROLER **********/

/* media info resources */
const MEDIA_INFOS_ID = "media_infos"
const MEDIA_INFO_TEMPLATE_ID = "media_info_template"

class MediaInfos {
    constructor(gps_ref) {
        this.id = MEDIA_INFOS_ID;
        this.logHeader = "MediaInfos : " + this.id + ": ";
        this.media_helper = new MediaHelper(this.id, MEDIA_INFO_TEMPLATE_ID, gps_ref);
        try {
            this.elements = {
                MEDIA_INFOS_ID: document.getElementById(this.id),
                MEDIA_INFO_TEMPLATE_ID: document.getElementById(MEDIA_INFO_TEMPLATE_ID)
            }
            window.addEventListener(ALBUM_CLOSE_EVENT, function(e) {
                console.debug(this.logHeader + 'receive message: ' + ALBUM_CLOSE_EVENT);
                this.media_helper.clear();
            }.bind(this));
            window.addEventListener(ALBUM_OPEN_EVENT, function(e) {
                console.debug(this.logHeader + 'receive message: ' + ALBUM_OPEN_EVENT + ' detail: ' + e.detail.id);
                this.get(e.detail.id);
            }.bind(this));
            window.addEventListener(MEDIA_FOCUS_EVENT, function(e) {
                console.debug(this.logHeader + 'receive message: ' + MEDIA_FOCUS_EVENT + ' detail: ' + e.detail.id);
                this.media_helper.focusToMedia(e.detail.id);
            }.bind(this));
            window.addEventListener(MEDIA_UNFOCUS_EVENT, function(e) {
                console.debug(this.logHeader + 'receive message: ' + MEDIA_UNFOCUS_EVENT + ' detail: ' + e.detail.id);
                this.media_helper.unfocusFromMedia(e.detail.id);
            }.bind(this));
        } catch (e) {
            console.debug(this.logHeader + " constructor fail with error:" + e.message);
        }
    }

    get(album) {
        console.debug(this.logHeader + 'get medias infos for ' + album);
        const xmlhttp = new XMLHttpRequest();
        var media_info = this;
        xmlhttp.onload = function() {
            var medias_info_data = JSON.parse(this.responseText);
            console.debug(this.responseText);
            var path_to_data = PATH_TO_MEDIA + '/' + album;
            media_info.media_helper.add(medias_info_data, path_to_data);
        };
        xmlhttp.open('GET', GET_MEDIA_INFOS_API + album);
        xmlhttp.send();
    }

    add(medias_info_data, path_to_data = "") {
        console.debug(this.logHeader + "add medias infos");
        this.media_helper.add(medias_info_data, path_to_data);
    }
}

/********** MEDIA DETAILS CONTROLER **********/

/* media details resources */
const MEDIA_DETAILS_ID = "media_details"

class MediaDetails extends ActionController {
    constructor() {
        super();
        this.id = MEDIA_DETAILS_ID;
        this.logHeader = "MediaDetails: " + this.id + ": ";
        try {
            this.elements = {
                MEDIA_DETAILS_ID : document.getElementById(this.id)
            }
            window.addEventListener(ALBUM_CLOSE_EVENT, function(e) {
                console.debug(this.logHeader + 'receive message: ' + ALBUM_CLOSE_EVENT);
                this.clear();
            }.bind(this));
        } catch (e) {
            console.debug(this.logHeader + " constructor fail with error:" + e.message);
        }
    }

    clear() {
        console.debug(this.logHeader + " clear");
        if (! this._assertDivFound()) return;
        this.elements.MEDIA_DETAILS_ID.setAttribute('srcdoc', '');
        console.debug(this.logHeader + " cleared");
      }
}

/********** MAP CONTROLER**********/

/* map resources */
const MAP_ID = "map"

class MapControler {
    constructor(center = {latitude:0.0,longitude:0.0}, zoom = 5) {
        this.id = MAP_ID;
        this.logHeader = "MapControler: " + this.id + ": ";
        this.center = center;
        this.zoom = zoom;
        this.mapHelper = new MapHelper(this.id, this.center, this.zoom);
        this.mapHelper.setCenter();
        this.mapHelper.focusToCenter();
        try {
            window.addEventListener(ALBUM_CLOSE_EVENT, function(e) {
                console.debug(this.logHeader + 'receive message: ' + ALBUM_CLOSE_EVENT);
                this.mapHelper.focusToCenter();
                this.mapHelper.clear();
            }.bind(this));
            window.addEventListener(MARKER_FOCUS_EVENT, function(e) {
                console.debug(this.logHeader + 'receive message: ' + MARKER_FOCUS_EVENT + ' id: ' + e.detail.id);
                this.mapHelper.focusToMarker(e.detail.id);
            }.bind(this));
            window.addEventListener(MARKER_UNFOCUS_EVENT, function(e) {
                console.debug(this.logHeader + 'receive message: ' + MARKER_UNFOCUS_EVENT + ' id: ' + e.detail.id);
                this.mapHelper.unfocusFromMarker(e.detail.id);
            }.bind(this));
            window.addEventListener(MARKER_ADD_EVENT, function(e) {
                console.debug(this.logHeader + 'receive message: ' + MARKER_ADD_EVENT + ' id: ' + e.detail.id);
                this.mapHelper.addMarker(e.detail.id, e.detail.latitude, e.detail.longitude);
            }.bind(this));
        } catch (e) {
            console.debug(this.logHeader + " constructor fail with error:" + e.message);
        }
    }
}
