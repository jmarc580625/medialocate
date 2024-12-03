import os
import sys
import json
import logging
import argparse
import webbrowser
import socketserver
from typing import Dict, Optional
from urllib.parse import urlparse
from urllib.request import urlopen, Request
from urllib.error import URLError
from http.server import SimpleHTTPRequestHandler
from medialocate.util.file_naming import get_hash, to_posix, to_uri
from medialocate.util.url_validator import validate_query
from medialocate.finder.file import FileFinder
from medialocate.media.parameters import MEDIALOCATION_STORE_NAME

"""
TODO:

# Generate SSL certificate:
openssl req -newkey rsa:2048 -nodes -keyout key.pem -x509 -days 365 -out certificate.pem

# Use SSL in HTTPServer:
import ssl
httpd = HTTPServer(('localhost', 443), MyHandler)
httpd.socket = ssl.wrap_socket(
    httpd.socket,
    server_side=True,
    certfile="certificate.pem",
    keyfile="key.pem"
)
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


class MediaHTTPServer(socketserver.TCPServer):
    def __init__(self, server_address, RequestHandlerClass):
        self.working_directory = ""
        self.data_root_dir = ""
        self.items_dict = {}
        super().__init__(server_address, RequestHandlerClass)


class ServiceHandler(SimpleHTTPRequestHandler):
    log: logging.Logger = logging.getLogger(MEDIASERVER_LOGGER)

    def translate_path(self, path: str) -> str:
        if path.startswith("/media/"):
            self.log.debug(f"translate_path from: path={path}")
            path = path.replace("/media/", "")
            path = super().translate_path(path)
            path = path[len(self.server.working_directory) + 1 :]  # type: ignore
            path = os.path.join(self.server.data_root_dir, path)  # type: ignore
            self.log.debug(f"translate_path to: path={path}")
            return path
        else:
            return super().translate_path(path)

    def _album_query_2_path(
        self, album_resource_name: str
    ) -> tuple[Optional[str], int, str]:
        # empty url query
        if not album_resource_name:
            return (None, 400, "Missing query")

        # Prevent directory traversal
        is_valid, message = validate_query(album_resource_name)
        if not is_valid:
            return (None, 400, message)

        # check album exist
        from pathlib import Path

        album_name = Path(album_resource_name).parts[0]
        if album_name not in self.server.items_dict:  # type: ignore
            return (None, 404, f"URL error: {album_resource_name} not found")

        # check file exists
        root_dir = self.server.data_root_dir  # type: ignore
        path = to_posix(os.path.join(root_dir, album_resource_name))
        if not os.path.exists(path):
            return (None, 404, f"URL error: {album_resource_name} not found")

        return (path, 0, "")

    def _validate_url_scheme(self, url: str) -> bool:
        """Validate URL scheme"""
        try:
            parsed = urlparse(url)
            if parsed.scheme not in ["http", "https", "file"]:
                return False
            return True

        except Exception as e:
            self.log.error(f"URL validation error: {str(e)}")
            return False

    def do_GET(self) -> None:
        """Handle GET requests with special API endpoints and file serving."""
        try:
            parsed = urlparse(self.path)
            path = parsed.path
            query_string = parsed.query

            # Handle special API endpoints
            if path == "/api/shutdown":
                self._handle_shutdown()
            elif path == "/api/media/albums":
                self._handle_albums()
            elif path == "/api/media/album":
                self._handle_album(query_string)
            elif path == "/proxy":
                self._handle_proxy(query_string)
            else:
                # Handle regular file serving
                super().do_GET()
        except Exception as e:
            self.log.error(f"Error handling request: {str(e)}")
            self.send_error(500, str(e))

    def _handle_proxy(self, query_string: str) -> None:
        """Handle proxy requests with support for range requests and streaming."""
        self.log.debug(f"GET: /proxy?{query_string}")

        path, code, message = self._album_query_2_path(query_string)
        if path is None:
            self.send_error(code, message)
            return

        url = to_uri(path)
        # Validate URL scheme and path
        if not self._validate_url_scheme(url):
            self.send_error(400, "Invalid URL")
            return

        try:
            # Get range header if present
            range_header = self.headers.get("Range")

            # Use Request to set User-Agent and other headers
            headers = {
                "User-Agent": "MediaLocate/1.0",
            }
            if range_header:
                headers["Range"] = range_header

            req = Request(url, headers=headers)

            # Open URL with timeout
            with urlopen(
                req, timeout=10
            ) as response:  # nosec B310 - URL scheme is validated
                content_length = response.headers.get("Content-Length")
                content_type = response.headers.get(
                    "Content-Type", "application/octet-stream"
                )
                accept_ranges = response.headers.get("Accept-Ranges")

                # Handle range response
                if range_header and response.status == 206:  # Partial Content
                    self.send_response(206)
                    self.send_header("Content-Range", response.headers["Content-Range"])
                    self.send_header("Content-Length", content_length)
                else:
                    self.send_response(200)
                    if content_length:
                        self.send_header("Content-Length", content_length)
                    if accept_ranges:
                        self.send_header("Accept-Ranges", accept_ranges)

                self.send_header("Content-type", content_type)
                self.end_headers()

                # Stream the response
                self._stream_response(response, content_type)

        except URLError as e:
            self.log.error(f"URL error: {str(e)}")
            self.send_error(400, f"URL error: {str(e)}")
        except Exception as e:
            self.log.error(f"Proxy error: {str(e)}")
            self.send_error(500, f"Proxy error: {str(e)}")

    def _handle_shutdown(self) -> None:
        """Handle shutdown API endpoint."""
        self.log.debug("GET: /api/shutdown")
        self.send_response(200)
        self.send_header("Content-type", "application/json")
        self.end_headers()
        self.wfile.write(bytes('{"shutdown":"ack"}', "utf-8"))
        sys.exit(0)

    def _handle_albums(self) -> None:
        """Handle albums API endpoint."""
        self.log.debug("GET: /api/media/albums")
        self.send_response(200)
        self.send_header("Content-type", "application/json")
        self.end_headers()
        out = json.dumps(self.server.items_dict)  # type: ignore
        self.wfile.write(bytes(out, "utf-8"))

    def _handle_album(self, query_string: str) -> None:
        """Handle single album API endpoint."""
        self.log.debug(f"GET: /api/media/album?{query_string}")

        path, code, message = self._album_query_2_path(query_string)
        if path is None:
            self.send_error(code, message)
            return

        path = os.path.join(path, self.server.items_dict[query_string])  # type: ignore
        if not os.path.isfile(path):
            self.send_error(404, "Album not found")
            return

        try:
            with open(path, "rb") as file:
                self.send_response(200)
                self.send_header("Content-type", "application/json")
                self.end_headers()
                self.wfile.write(file.read())
        except Exception as e:
            self.log.error(f"Error serving album: {str(e)}")
            self.send_error(500, "Error serving album")

    def _stream_response(self, response, content_type: str) -> None:
        """Stream response with appropriate handling based on content type."""
        try:
            # For video/audio content, use smaller chunks for better streaming
            if content_type.startswith(("video/", "audio/")):
                chunk_size = 64 * 1024  # 64KB chunks for media
            else:
                chunk_size = 256 * 1024  # 256KB chunks for other content

            while True:
                chunk = response.read(chunk_size)
                if not chunk:
                    break
                self.wfile.write(chunk)

        except ConnectionError:
            # Client disconnected, which is normal for range requests
            self.log.debug("Client disconnected during streaming")
        except Exception as e:
            self.log.error(f"Error during streaming: {str(e)}")
            raise


class MediaServer:
    port: int
    log: logging.Logger
    cache_dir: str
    working_directory: str
    data_root_dir: str
    session_cache: str
    items_dict: Dict[str, str]
    httpd: Optional[socketserver.TCPServer]
    launch_browser: bool

    def __init__(
        self,
        port: int,
        data_root_dir: str,
        log: Optional[logging.Logger] = None,
        launch_browser: bool = False,
    ) -> None:
        self.port = port
        self.log = log or logging.getLogger(MEDIASERVER_LOGGER)
        self.cache_dir = os.path.join(os.path.expanduser("~"), MEDIASERVER_SESSION_DIR)
        self.working_directory = os.path.join(
            os.path.dirname(__file__), MEDIASERVER_UX_DIR
        )
        abs_path_to_data_root_dir = os.path.abspath(data_root_dir)
        self.data_root_dir = os.path.normpath(abs_path_to_data_root_dir)
        self.session_cache = os.path.join(
            self.cache_dir, f"{get_hash(self.data_root_dir)}.json"
        )
        self.items_dict: Dict[str, str] = {}
        self.httpd: Optional[socketserver.TCPServer] = None
        self.launch_browser = launch_browser

    def get_media_sources(self, directory: str) -> Dict[str, str]:
        path_to_data_length = len(directory.split(os.sep))
        items_dict: Dict[str, str] = {}

        for item in FileFinder(directory, matches=[MEDIALOCATION_STORE_NAME]).find():
            self.log.info(f"{item}")
            path_items = item.split(os.sep)
            # Split path into value (last 2 components) and key (middle components)
            # TODO: initial version, need validate path before remove
            # value = os.sep.join(path_items[len(path_items) - 2 :])
            # key = os.sep.join(path_items[path_to_data_length : len(path_items) - 2])
            value = os.sep.join(path_items[-2:])
            key = os.sep.join(path_items[path_to_data_length:-2])
            items_dict[to_posix(key)] = to_posix(value)

        return items_dict

    def save_media_sources(self, items_dict: Dict[str, str]) -> None:
        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir)
        with open(self.session_cache, "w") as f:
            json.dump(self.items_dict, f, indent=2)

    def retrieve_media_sources(self) -> None:
        if os.path.exists(self.session_cache):
            with open(self.session_cache, "r") as f:
                self.items_dict = json.load(f)

    def initiate(self) -> None:
        self.retrieve_media_sources()
        if not self.items_dict:
            self.items_dict = self.get_media_sources(self.data_root_dir)
            self.save_media_sources(self.items_dict)

    def start(self) -> None:
        self.initiate()
        os.chdir(self.working_directory)
        with MediaHTTPServer(("", self.port), ServiceHandler) as httpd:
            self.httpd = httpd
            httpd.working_directory = self.working_directory
            httpd.data_root_dir = self.data_root_dir
            httpd.items_dict = self.items_dict
            url = f"{MEDIASERVER_UX}:{self.port}"
            if self.launch_browser:
                try:
                    webbrowser.open(url)
                except Exception as e:
                    self.log.error(f"Failed to open browser: {e}")
            httpd.serve_forever()


def main(
    port: int, directory: str, log: logging.Logger, launch_browser: bool = False
) -> None:
    server = MediaServer(port, directory, log)
    server.start()


if __name__ == "__main__":
    help_text = """
    Media server for serving media files and location data through a web interface.
    """
    parser = argparse.ArgumentParser(
        description=help_text, formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument(
        "-p", default=MEDIASERVER_PORT, type=int, help="port number to listen on"
    )
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
