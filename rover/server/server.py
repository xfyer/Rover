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
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(bytes("<html><head><title>Testing</title></head>", "utf-8"))
        self.wfile.write(bytes("<body>", "utf-8"))
        self.wfile.write(bytes("<p>Request: %s</p>" % self.path, "utf-8"))
        self.wfile.write(bytes("<p>Current Time: {current_time}</p>".format(current_time=f"{datetime.now().astimezone(tz=pytz.UTC):%A, %B, %d %Y at %H:%M:%S.%f %z}"), "utf-8"))
        self.wfile.write(bytes("<h1>Please Visit Me On <a href=\"https://twitter.com/DigitalRoverDog\">Twitter</a> For The Currently Implemented Features!!!</h1>" % self.path, "utf-8"))
        self.wfile.write(bytes("</body></html>", "utf-8"))
