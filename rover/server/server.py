#!/usr/bin/python

import logging
import socketserver
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Tuple

from doltpy.core.system_helpers import get_logger

from config import config as main_config
import rover.server.page_handler as handler
import rover.server.api_handler as api

threadLock: threading.Lock = threading.Lock()


class WebServer(threading.Thread):
    def __init__(self, threadID, name, counter):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.name = name
        self.counter = counter

        self.logger: logging.Logger = get_logger(__name__)
        self.INFO_QUIET: int = main_config.INFO_QUIET
        self.VERBOSE: int = main_config.VERBOSE

        self.host_name = "0.0.0.0"
        self.port = 8930

    def run(self):
        self.logger.log(self.INFO_QUIET, "Starting " + self.name)

        # Get lock to synchronize threads
        threadLock.acquire()

        webServer = HTTPServer((self.host_name, self.port), RequestHandler)
        self.logger.log(self.INFO_QUIET, "Server Started %s:%s" % (self.host_name, self.port))

        try:
            webServer.serve_forever()
        except KeyboardInterrupt as e:
            raise e  # TODO: Figure Out How To Prevent Need To Kill Twice

        webServer.server_close()
        self.logger.log(self.INFO_QUIET, "Server Stopped")

        # Free lock to release next thread
        threadLock.release()


class RequestHandler(BaseHTTPRequestHandler):
    def __init__(self, request: bytes, client_address: Tuple[str, int], server: socketserver.BaseServer):
        self.logger: logging.Logger = get_logger(__name__)
        self.INFO_QUIET: int = main_config.INFO_QUIET
        self.VERBOSE: int = main_config.VERBOSE

        super().__init__(request, client_address, server)

    def log_message(self, log_format, *args):
        self.logger.log(logging.DEBUG, log_format % args)

    def do_GET(self):
        try:
            if self.path.lower().startswith("/api/"):
                api.handle_api(self=self)
            elif self.path.lower() == "/manifest.webmanifest":
                handler.load_file(self=self, path="rover/server/web/other/manifest.json", mime_type="application/manifest+json")
            elif self.path.lower() == "/robots.txt":
                handler.load_file(self=self, path="rover/server/web/other/robots.txt", mime_type="text/plain")
            elif self.path.lower() == "/favicon.ico":
                handler.load_404_page(self=self)
            elif self.path.lower() == "/images/rover.png":
                handler.load_file(self=self, path="rover/server/web/images/Rover.png", mime_type="image/png")
            elif self.path.lower() == "/images/rover.svg":
                handler.load_file(self=self, path="rover/server/web/images/Rover.svg", mime_type="image/svg+xml")
            elif self.path.lower() == "/css/stylesheet.css":
                handler.load_file(self=self, path="rover/server/web/css/stylesheet.css", mime_type="text/css")
            else:
                handler.load_page(self=self)
        except BrokenPipeError as e:
            self.logger.debug("{ip_address} Requested {page_url}: {error_message}".format(ip_address=self.address_string(), page_url=self.path, error_message=e))

    def version_string(self):
        return "Rover"
