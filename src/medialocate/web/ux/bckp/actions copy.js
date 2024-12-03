class MediaAlbums {
    constructor() {
        this.divId = "media_albums";
        this.httpAction = 'GET';
        this.httpActionParameter = "/api/media/albums";
        this.list = null;
        this.div = null;
        try {
            this.div = document.getElementById(divId);
        } catch (e) {
            console.log(e);
        }
        window.onmessage = function(e) {
            if (e.data == "close") {
                this.hide();
            }
        }.bind(this);
    }

    _assertDivFound() {
        if (this.div == null) {
            console.log("MediaAlbums div " + this.divId + " not found");
            return false;
        }
        return true;
    }
 
    get(event) {
        if (! this._assertDivFound()) return;
        console.log('get medias albums');
        const xmlhttp = new XMLHttpRequest();
        xmlhttp.onload = function() {
            console.log('load medias albums');
            const myObj = JSON.parse(this.responseText);
            container = document.createElement("div");
            list = document.createElement("ul");
            container.appendChild(list);
            for (var key in myObj) {
                var value = myObj[key];
                item = document.createElement("li");
                itemText = document.createTextNode(key);
                itemLink = document.createElement("a");
                itemLink.href = "javascript:void(0)";
                itemLink.onclick = function() {getMedias(); }
                itemLink.appendChild(itemText);
                item.appendChild(itemLink);
                list.appendChild(item);
            }
            this.list = list;
            this.div.appendChild(container);
        };
        xmlhttp.open(this.httpAction, this.httpActionParameter);
        xmlhttp.send();
    }

    show() {
        if (! this._assertDivFound()) return;
        if (this.list == null) {
            this.get();
        }
        this.div.style.visibility = "visible";
        console.log('show element with id ' + this.divId);
    }

    hide() {
        if (! this._assertDivFound()) return;
        this.list.style.visibility = "hidden";
        console.log('hide element with id ' + this.divId);
    }
}

var medias_list = null;

function showMediasList() {
    if (medias_list == null) {
        getMediasList();
    }
    open_div = document.getElementById("open_div");
    open_div.style.visibility = "visible";
}

function getMediasList() {
    console.log('in get_medias_list()');
    const xmlhttp = new XMLHttpRequest();
    xmlhttp.onload = function() {
        console.log('in onload_medias_list()');
        const myObj = JSON.parse(this.responseText);
        open_div_content = document.getElementById("open_div_content");
        list = document.createElement("ul");
        for (var key in myObj) {
            var value = myObj[key];
            item = document.createElement("li");
            itemText = document.createTextNode(key);
            itemLink = document.createElement("a");
            itemLink.href = "javascript:void(0)";
            itemLink.onclick = function() {getMedias(); }
            //itemLink.onclick = "getMedias()";
            itemLink.appendChild(itemText);
            item.appendChild(itemLink);
            list.appendChild(item);
            medias_list = list;
        }
        open_div_content.appendChild(list);
    };
    xmlhttp.open("GET", "/api/list");
    xmlhttp.send();
}

class MediaInfos {
    constructor(divId) {
        this.divId = "media_infos";
        this.divTemplateId = "media_info_template";
        this.httpAction = 'GET';
        this.httpActionParameter = "/api/media/album?";
        this.div = null;
        this.template = null;
        try {
            this.div = document.getElementById(this.divId);
            this.template = document.getElementById(this.divTemplateId);
        } catch (e) {
            console.log(e);
        }
    }

    _assertDivFound() {
        if (this.div == null || this.template == null) {
            if (this.div == null) console.log("MediaInfos div " + this.divId + " not found");
            if (this.template == null) console.log("MediaInfos template " + this.divTemplateId + " not found");
            return false;
        }
        return true;
    }

    get(name) {
        if (! this._assertDivFound()) return;
        console.log('get medias infos for ' + name);
        const xmlhttp = new XMLHttpRequest();
        xmlhttp.onload = function() {
            medias_info_data = JSON.parse(this.responseText);
            console.log(this.responseText);
            //console.log('medialocate_data_dir = ' + medialocate_data_dir);
            initializeContent(
                this.div,
                this.template,
                medias_info_data,
                gpsOrigin,                          // gpsOrigin is GLOBAL VARIABLE !
                path_to_data = "media/" + name
            );
            setMediasName(name);
        };
        xmlhttp.open(this.httpAction, this.httpActionParameter + name);
        xmlhttp.send();
    }

    open(event) {
        if (! this._assertDivFound()) return;
        this.clear();
        this.get(event.target.innerText);
        console.log('open medias infos in ' + this.divId);
    }

    clear() {
        if (! this._assertDivFound()) return;
        while (this.div.firstChild) {
            this.div.removeChild(conteneur.firstChild);
        }
        this.div.contentWindow.postMessage('clear', '*');
        console.log('clear medias infos in ' + this.divId);

        setMediasName('');
        clearMediasDetails();
        clearMap();
        centerMap();
    }
}


function getMedias() {
    name = event.target.innerText;
    console.log('getMedias for ' + name);
    open_div.style.visibility = "hidden";
    const xmlhttp = new XMLHttpRequest();
    xmlhttp.onload = function() {
        medialocate_data = JSON.parse(this.responseText);
        console.log(this.responseText);
        //console.log('medialocate_data_dir = ' + medialocate_data_dir);
        clearAll();
        initializeContent(
            document.getElementById('medias'),
            document.getElementsByTagName("template")[0],
            medialocate_data,
            gpsOrigin,
            path_to_data = "media/" + name
        );
        setMediasName(name);
    };
    xmlhttp.open("GET", "/api/open?" + name);
    xmlhttp.send();
}

function confirmExit() {
    if (confirm('Are you sure you want to exit?')) {
        console.log('exit confirmed');
        const xmlhttp = new XMLHttpRequest();
        xmlhttp.onload = function() {
            console.log('exit acknowledged');
            window.close();
        };
        xmlhttp.open("GET", "/api/shutdown");
        xmlhttp.send();
    }
}

function confirmClose() {
    clearAll();
}

function clearAll() {
    clearMedias();
    clearMap();
    clearMediasDetails();
    centerMap();
    setMediasName('');
}



class MediaDetails {
    constructor(divId) {
        this.frameId = "media_details";
        this.frame = null;
        try {
            this.frame = document.getElementById(this.frameId);
        } catch (e) {
            console.log(e);
        }
        window.onmessage = function(e) {
            if (e.data == "close") {
                this.clear();
            }
        }.bind(this);
    }

    _assertDivFound() {
        if (this.frame == null) {
            console.log("MediaDetails div " + this.frameId + " not found");
            return false;
        }
        return true;
    }

    clear() {
        this.frame.setAttribute('srcdoc', '');
        console.log('media details frame " + this.frameId + " cleared');
      }
}


class Menu {
    constructor() {
        this.httpAction = 'GET';
        this.httpActionParameter = "/api/shutdown";
        this.divId = "menu";
        this.open = null;
        this.close = null;
        this.exit = null;
        this.div = null;
        try {
            this.div = document.getElementById(divId);
            this.name = document.getElementById("menu_medias_name");
            this.open = document.getElementById("menu_open");
            this.close = document.getElementById("menu_close");
            this.exit = document.getElementById("menu_exit");
        } catch (e) {
            console.log(e);
        }
        this.open.onclick = function() {this.open();}.bind(this);
        this.close.onclick = function() {this.close();}.bind(this);
        this.exit.onclick = function() {this.exit();}.bind(this);
    }

    _assertDivFound() {
        if (this.div == null || this.name == null) {
                if (this.div == null) console.log("Menu div " + this.divId + " not found");
                if (this.name == null) console.log("Menu name " + this.nameId + " not found");
            return false;
        }
        return true;
    }

    exit() {
        if (confirm('Are you sure you want to exit?')) {
            console.log('exit confirmed');
            const xmlhttp = new XMLHttpRequest();
            xmlhttp.onload = function() {
                console.log('exit acknowledged');
                window.close();
            };
            xmlhttp.open(this.httpAction, this.httpActionParameter);
            xmlhttp.send();
        }
    }
    
    close() {
        this.div.contentWindow.postMessage('clear', '*');
        console.log('close action from menu');
    }
    
    open() {
        this.div.contentWindow.postMessage('open', '*');
        console.log('close action from menu');
    }

}
