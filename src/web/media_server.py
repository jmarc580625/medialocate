import os
import sys
import json
import logging
import argparse
from urllib.request import urlopen
import socketserver
from http.server import SimpleHTTPRequestHandler

from util.file_naming import get_hash, to_posix
from finder.file import FileFinder
from media.parameters import MEDIALOCATION_STORE_NAME

"""
TODO:

openssl req -newkey rsa:2048 -nodes -keyout key.pem -x509 -days 365 -out certificate.pem

import ssl
httpd = HTTPServer(('localhost', 443), MyHandler)
httpd.socket = ssl.wrap_socket(httpd.socket, server_side=True, certfile="certificate.pem", keyfile="key.pem")
httpd.serve_forever()

"""
# -------------------------------------------------------------------------------
# parameters
# -------------------------------------------------------------------------------
MEDIASERVER = "mediaserver"
MEDIASERVER_PORT = 8080
MEDIASERVER_UX = "http://localhost"
MEDIASERVER_UX_DIR = "ux"
MEDIASERVER_LOGGER = MEDIASERVER
MEDIASERVER_SESSION_DIR = f".{MEDIASERVER}"

"""
SimpleHTTPRequestHandler.extensions_map.update({
    '': 'application/octet-stream',
    '.json': 'application/json',
    '.html': 'text/html',
    '.css': 'text/css',
    '.js': 'application/x-javascript',
    '.wasm': 'application/wasm',
    '.svg': 'image/svg+xml',
})
"""
server: "MediaServer" = None


class ServiceHandler(SimpleHTTPRequestHandler):

    def translate_path(self, path: str) -> str:
        if path.startswith("/media/"):
            log.debug(f"translate_path from: path={path}")
            path = path.replace("/media/", "")
            path = super().translate_path(path)
            path = path[len(server.working_directory) + 1 :]
            path = os.path.join(server.data_root_dir, path)
            log.debug(f"translate_path to: path={path}")
            return path
        else:
            return super().translate_path(path)

    def do_GET(self: "ServiceHandler") -> None:
        from urllib.parse import urlparse

        log.debug(f"path={self.path}")
        parsed = urlparse(self.path)
        query_string = parsed.query
        path = parsed.path
        if path == "/api/shutdown":
            log.debug("GET: " + path)
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            self.wfile.write(bytes('{"shutdown":"ack"}', "utf-8"))
            # server.httpd.shutdown()
            sys.exit(0)
        elif path == "/api/media/albums":
            log.debug("GET: " + path)
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            out = json.dumps(server.items_dict)
            self.wfile.write(bytes(out, "utf-8"))
        elif path == "/api/media/album":
            log.debug("GET: " + path + "?" + query_string)
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            path = os.path.join(server.data_root_dir, query_string)
            path = os.path.join(path, server.items_dict[query_string])
            with open(path, "rb") as file:
                self.wfile.write(file.read())
                self.wfile.write(file.read())
        elif path == "/proxy":
            log.debug("GET: " + path + "?" + query_string)
            self.copyfile(urlopen(query_string), self.wfile)
        else:
            try:
                super().do_GET()
            except Exception as e:
                log.error(e)


class MediaServer:

    def __init__(self: "MediaServer", port: int, data_root_dir: str, log: logging.Logger) -> None:
        self.port = port
        self.log = log
        self.cache_dir = os.path.join(os.path.expanduser("~"), MEDIASERVER_SESSION_DIR)
        self.working_directory = os.path.join(os.path.dirname(__file__), MEDIASERVER_UX_DIR)
        abs_path_to_data_root_dir = os.path.abspath(data_root_dir)
        self.data_root_dir = os.path.normpath(abs_path_to_data_root_dir)
        self.session_cache = os.path.join(self.cache_dir, f"{get_hash(self.data_root_dir)}.json")
        self.items_dict = None
        self.httpd = None

    def get_media_sources(self: "MediaServer", directory: str) -> dict[str, str]:
        path_to_data_length = len(directory.split(os.sep))
        items_dict = {}

        for item in FileFinder(directory, matches=[MEDIALOCATION_STORE_NAME]).find():
            log.info(f"{item}")
            path_items = item.split(os.sep)
            value = os.sep.join(path_items[len(path_items) - 2 :])
            key = os.sep.join(path_items[path_to_data_length : len(path_items) - 2])
            items_dict[to_posix(key)] = to_posix(value)

        return items_dict

    def save_media_sources(self: "MediaServer", items_dict: dict[str, str]) -> None:
        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir)
        with open(self.session_cache, "w") as f:
            json.dump(self.items_dict, f, indent=2)

    def retrieve_media_sources(self: "MediaServer") -> dict[str, str]:
        if os.path.exists(self.session_cache):
            with open(self.session_cache, "r") as f:
                self.items_dict = json.load(f)

    def initiate(self: "MediaServer") -> None:
        self.retrieve_media_sources()
        if self.items_dict is None:
            self.items_dict = self.get_media_sources(self.data_root_dir)
            self.save_media_sources(self.items_dict)

    def start(self: "MediaServer") -> None:
        self.initiate()
        os.chdir(self.working_directory)
        with socketserver.TCPServer(("", self.port), ServiceHandler) as self.httpd:
            os.system(f" start {MEDIASERVER_UX}:{self.port} ")
            self.httpd.serve_forever()


def main(port: int, directory: str, log: logging.Logger) -> None:

    global server
    server = MediaServer(port, directory, log)
    server.start()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description=help, formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument("-p", default=MEDIASERVER_PORT, type=int, help="port number to listen on")
    parser.add_argument("-d", default=".", type=str, help="path to the directory")
    args = parser.parse_args()

    # logging.basicConfig(level = logging.NOTSET)
    logging.basicConfig(
        format="%(asctime)s : %(levelname)-8s : %(name)s : %(message)s",
        level=logging.NOTSET,
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    log = logging.getLogger(MEDIASERVER_LOGGER)
    log.debug(", ".join(f"{arg}={getattr(args, arg)}" for arg in vars(args)))

    main(args.p, args.d, log)
