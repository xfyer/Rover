#!/usr/bin/python

import logging
import socketserver
import threading
import humanize

from datetime import datetime
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Tuple

import pytz
from doltpy.core.system_helpers import get_logger
from config import config as main_config

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
        super().__init__(request, client_address, server)

    def log_message(self, log_format, *args):
        return

    def do_GET(self):
        # TODO: Add CSS and Hosting Own Images Support

        # Site Data
        site_title: str = "Rover"
        site_icon: str = "https://raw.githubusercontent.com/alexis-evelyn/Rover/master/rover/server/images/Rover.png"

        # Twitter Metadata
        twitter_title: str = site_title
        twitter_description: str = "Future Analysis Website Here!!!"
        twitter_icon: str = site_icon

        # Current Time
        current_time: str = f"{datetime.now().astimezone(tz=pytz.UTC):%A, %B, %d %Y at %H:%M:%S.%f %z}"
        background_color: str = "#000000"
        text_color: str = "#ffffff"

        # HTTP Headers
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()

        # Header
        self.wfile.write(bytes("<html><head>", "utf-8"))
        self.wfile.write(bytes(f"<title>{site_title}</title>", "utf-8"))
        self.wfile.write(bytes(f"<link rel=\"icon\" type=\"image/png\" href=\"{site_icon}\">", "utf-8"))

        # Twitter Cards - https://medium.com/@dinojoaocosta/how-to-make-twitter-preview-your-website-links-5b20db98ac4f
        self.wfile.write(bytes("<meta name=\"twitter:card\" content=\"summary\" />", "utf-8"))
        self.wfile.write(bytes("<meta name=\"twitter:site\" content=\"@AlexisEvelyn42\" />", "utf-8"))
        self.wfile.write(bytes(f"<meta name=\"twitter:title\" content=\"{twitter_title}\" />", "utf-8"))
        self.wfile.write(bytes(f"<meta name=\"twitter:description\" content=\"{twitter_description}\" />", "utf-8"))
        self.wfile.write(bytes(f"<meta name=\"twitter:image\" content=\"{twitter_icon}\" />", "utf-8"))

        self.wfile.write(bytes("</head>", "utf-8"))

        # Body
        self.wfile.write(bytes(f"<body text=\"{text_color}\" bgcolor=\"{background_color}\">", "utf-8"))
        self.wfile.write(bytes(f"<p>Request: {self.path}</p>", "utf-8"))
        self.wfile.write(bytes(f"<p>Current Time: {current_time}</p>", "utf-8"))
        self.wfile.write(bytes("<h1>Please Visit Me On <a href=\"https://twitter.com/DigitalRoverDog\">Twitter</a> For The Currently Implemented Features!!!</h1>", "utf-8"))
        self.wfile.write(bytes("</body></html>", "utf-8"))
