"""HTTP server implementation for serving media files and location data through a web interface.

This module provides a web server that serves media files and associated location data through
a RESTful API. It includes the following main components:

- MediaServer: Main server class that handles initialization and server lifecycle
- ServiceHandler: HTTP request handler with support for media streaming and API endpoints
- LimitedFileReader: Utility class for controlled streaming of large media files

The server supports:
- Media file streaming with range requests
- Album management and listing
- Session persistence
- Browser-based interface
"""

import os
import io
import json
import logging
import argparse
import threading
import webbrowser
import socketserver
from typing import Dict, Optional, Tuple
from pathlib import Path
from urllib.parse import urlparse
from http.server import SimpleHTTPRequestHandler
from medialocate.util.file_naming import (
    get_hash_from_native_path,
    relative_path_to_posix,
)
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


class MediaHTTPServer(socketserver.TCPServer):
    """TCP server implementation for handling media file requests.

    Extends TCPServer to provide media file serving capabilities with support for
    working directory, data root directory, and items dictionary management.
    """

    def __init__(self, server_address, RequestHandlerClass):
        """Initialize the MediaHTTPServer.

        Args:
            server_address: Tuple of (host, port) for the server to listen on
            RequestHandlerClass: Handler class for processing requests
        """
        self.working_directory = ""
        self.data_root_dir = ""
        self.items_dict = {}
        super().__init__(server_address, RequestHandlerClass)


class LimitedFileReader(io.RawIOBase):
    """A file-like object that limits the number of bytes that can be read."""

    def __init__(self, file_obj, remaining):
        """Initialize the LimitedFileReader.

        Args:
            file_obj: The file object to read from
            remaining: The maximum number of bytes that can be read
        """
        super().__init__()
        self.file_obj = file_obj
        self.remaining = remaining

    def readable(self) -> bool:
        """Check if the file object is readable.

        Returns:
            bool: Always returns True as this is a read-only file object
        """
        return True

    def read(self, size=None):
        """Read up to size bytes from the file object.

        Args:
            size: The maximum number of bytes to read. If None, read up to remaining bytes.

        Returns:
            bytes: The bytes read from the file object
        """
        if size is None or size > self.remaining:
            size = self.remaining
        if size <= 0:
            return b""
        data = self.file_obj.read(size)
        self.remaining -= len(data)
        return data


class ServiceHandler(SimpleHTTPRequestHandler):
    """HTTP request handler for media file serving and API endpoints.

    Extends SimpleHTTPRequestHandler to provide specialized handling for
    media files, album management, and API endpoints.
    """

    log: logging.Logger = logging.getLogger(MEDIASERVER_LOGGER)

    def _to_album_local_path(self, path: Path) -> str:
        path = Path(self.server.data_root_dir) / path  # type: ignore
        try:
            path.resolve(strict=True)
        except Exception as e:
            self.log.error(f"Path resolution error: {str(e)}")
            return ""
        return str(path)

    def translate_path(self, path: str) -> str:
        """Translate URL paths to filesystem paths.

        Args:
            path: URL path to translate

        Returns:
            str: Filesystem path or empty string if invalid
        """
        if path.startswith("/media/"):
            striped_path = path.replace("/media/", "")

            # empty url query
            if not striped_path:
                self.send_error(400, "Media file name missing")
                return ""

            # Prevent directory traversal
            valid, unquoted_path, message = validate_query(striped_path)
            if not valid:
                self.send_error(400, message)
                return ""

            path = self._to_album_local_path(
                Path(unquoted_path) if unquoted_path else Path()
            )
            return path if path else ""
        else:
            return super().translate_path(path)

    def _validate_query(self, query_string: str) -> Tuple[bool, int, str]:
        # empty url query
        if not query_string:
            return (False, 400, "Missing query")

        # Prevent directory traversal
        valid, unquoted_query, message = validate_query(query_string)
        if not valid:
            return (False, 400, message)
        return (True, 200, "")

    def _get_content_type(self, path):
        """Determine content type based on file extension."""
        ext = os.path.splitext(path)[1].lower()
        content_types = {
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".png": "image/png",
            ".gif": "image/gif",
            ".mp4": "video/mp4",
            ".avi": "video/x-msvideo",
            ".mov": "video/quicktime",
        }
        return content_types.get(ext, "application/octet-stream")

    def do_GET(self) -> None:
        """Handle GET requests for files and API endpoints.

        Processes requests for media files, album data, and server control.
        Supports range requests for media streaming.
        """
        try:
            parsed = urlparse(self.path)
            path = parsed.path
            query_string = parsed.query

            # Handle special API endpoints
            if path == "/api/shutdown":
                self._handle_shutdown()
            elif path == "/api/albums":
                self._handle_album_list()
            elif path == "/api/album":
                self._handle_album(query_string)
            elif path == "/api/media":
                self._handle_media(query_string)
            else:
                # Handle regular file serving
                super().do_GET()
        except Exception as e:
            self.log.error(f"Error handling request: {str(e)}")
            self.send_error(500, str(e))

    def _handle_media(self, query_string: str) -> None:
        """Handle media file requests with support for range requests and streaming."""
        try:
            self.log.debug(f"GET: /media?{query_string}")

            # empty url query
            if not query_string:
                self.send_error(400, "Missing query")
                return

            # check query validity and return unquoted query
            valid, query, message = validate_query(query_string)
            if not valid:
                self.send_error(400, message)
                return

            """
            album_name = os.path.dirname(query)
            media_name = os.path.basename(query)

            # check album exist
            album_dict = self.server.items_dict.get(album_name, None) # type: ignore
            if not album_dict:
                self.send_error(404, f"URL error: album {album_name} not found")
                return
            """

            # check media file exists
            path_to_media = self._to_album_local_path(Path(query) if query else Path())
            if not path_to_media:
                self.send_error(404, "File not found")
                self.log.error(f"File not found: {query}")
                return

            file_size = os.path.getsize(path_to_media)
            content_type = self._get_content_type(path_to_media)
            range_header = self.headers.get("Range")

            if range_header:
                # Parse range header
                try:
                    ranges = range_header.replace("bytes=", "").split("-")
                    start = int(ranges[0])
                    end = int(ranges[1]) if ranges[1] else file_size - 1
                except (ValueError, IndexError):
                    self.send_error(400, "Invalid range header")
                    return

                # Send partial content
                self.send_response(206)
                self.send_header("Content-Range", f"bytes {start}-{end}/{file_size}")
                self.send_header("Content-Length", str(end - start + 1))
            else:
                # Send full content
                self.send_response(200)
                self.send_header("Content-Length", str(file_size))

            self.send_header("Accept-Ranges", "bytes")
            self.send_header("Content-Type", content_type)
            self.end_headers()

            # Stream the file
            with open(path_to_media, "rb") as f:
                if range_header:
                    f.seek(start)
                    # Create a length-limited file-like object for partial content
                    file_obj = LimitedFileReader(f, end - start + 1)
                    f = io.BufferedReader(file_obj)
                self._stream_response(f, content_type)

        except Exception as e:
            # Log the full error with the Unicode path
            self.log.error(f"File error: {str(e)}")
            # Send a simplified ASCII-safe error message
            self.send_error(500, "Internal server error")

    def _handle_shutdown(self) -> None:
        """Handle shutdown API endpoint."""
        self.log.debug("GET: /api/shutdown")
        self.send_response(200)
        self.send_header("Content-type", "application/json")
        self.end_headers()
        self.wfile.write(bytes('{"shutdown":"ack"}', "utf-8"))

        # Start shutdown in a separate thread after response is sent
        threading.Thread(target=self.server.shutdown, daemon=True).start()

    def _handle_album_list(self) -> None:
        """Handle albums API endpoint."""
        self.log.debug("GET: /api/media/albums")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        out = json.dumps(self.server.items_dict)  # type: ignore
        self.wfile.write(bytes(out, "utf-8"))

    def _handle_album(self, query_string: str) -> None:
        """Handle single album API endpoint."""
        self.log.debug(f"GET: /api/media/album?{query_string}")

        # empty url query
        if not query_string:
            self.send_error(400, "Missing query")
            return

        # Prevent directory traversal
        valid, _, message = validate_query(query_string)
        if not valid:
            self.send_error(400, message)
            return

        # check album exist
        album_dict = self.server.items_dict.get(query_string, None)  # type: ignore
        if not album_dict:
            self.send_error(404, f"URL error: album {query_string} not found")
            return

        # check album dict exist
        album_dict_path = Path(query_string) / Path(album_dict)
        path = self._to_album_local_path(album_dict_path)

        if path is None:
            self.send_error(404, f"URL error: album file {path} not found")
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
    """Media server implementation for serving files and location data.

    Provides a web interface for accessing media files and associated location
    data through a RESTful API. Supports file streaming, album management,
    and session persistence.
    """

    def __init__(
        self,
        port: int,
        data_root_dir: str,
        log: Optional[logging.Logger] = None,
        launch_browser: bool = False,
    ) -> None:
        """Initialize the media server.

        Args:
            port: Port number to listen on
            data_root_dir: Root directory containing media files
            log: Optional logger instance
            launch_browser: Whether to launch browser on startup
        """
        self.port = port
        self.log = log or logging.getLogger(MEDIASERVER_LOGGER)
        self.cache_dir = os.path.join(os.path.expanduser("~"), MEDIASERVER_SESSION_DIR)
        self.working_directory = os.path.join(
            os.path.dirname(__file__), MEDIASERVER_UX_DIR
        )
        abs_path_to_data_root_dir = os.path.abspath(data_root_dir)
        self.data_root_dir = os.path.normpath(abs_path_to_data_root_dir)
        self.session_cache = os.path.join(
            self.cache_dir, f"{get_hash_from_native_path(self.data_root_dir)}.json"
        )
        self.items_dict: Dict[str, str] = {}
        self.httpd: Optional[socketserver.TCPServer] = None
        self.launch_browser = launch_browser

    def get_media_sources(self, directory: str) -> Dict[str, str]:
        """Get media sources from the specified directory.

        Args:
            directory: Directory to scan for media files

        Returns:
            Dict mapping album paths to media file locations
        """
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
            items_dict[relative_path_to_posix(key)] = relative_path_to_posix(value)

        return items_dict

    def save_media_sources(self, items_dict: Dict[str, str]) -> None:
        """Save media sources to the session cache.

        Args:
            items_dict: Dictionary of media sources to save
        """
        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir)
        with open(self.session_cache, "w") as f:
            json.dump(self.items_dict, f, indent=2)

    def retrieve_media_sources(self) -> None:
        """Load media sources from the session cache if available."""
        if os.path.exists(self.session_cache):
            with open(self.session_cache, "r") as f:
                self.items_dict = json.load(f)

    def initiate(self) -> None:
        """Initialize the server by loading or scanning media sources."""
        self.retrieve_media_sources()
        if not self.items_dict:
            self.items_dict = self.get_media_sources(self.data_root_dir)
            self.save_media_sources(self.items_dict)

    def start(self) -> None:
        """Start the media server and begin serving requests."""
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
    """Start the media server with the specified configuration.

    Args:
        port: Port number to listen on
        directory: Root directory containing media files
        log: Logger instance for output
        launch_browser: Whether to launch browser on startup
    """
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
