#!/usr/bin/python

from datetime import datetime
from pathlib import Path

import pytz

from rover import config


def load_page(self):
    # Site Data
    site_title: str = "Rover"

    # Twitter Metadata
    twitter_title: str = site_title
    twitter_description: str = "Future Analysis Website Here!!!"

    # Current Time
    current_time: str = f"{datetime.now().astimezone(tz=pytz.UTC):%A, %B, %d %Y at %H:%M:%S.%f %z}"

    # HTTP Headers
    self.send_response(200)
    self.send_header("Content-type", "text/html")
    self.end_headers()

    self.wfile.write(bytes(load_text_file("rover/server/web/templates/header.html")
                           .replace("{site_title}", site_title)
                           .replace("{twitter_title}", twitter_title)
                           .replace("{twitter_handle}", config.AUTHOR_TWITTER_HANDLE)
                           .replace("{twitter_description}", twitter_description)
                           , "utf-8"))

    # Body
    self.wfile.write(bytes(f"<p>Request: {self.path}</p>", "utf-8"))
    self.wfile.write(bytes(f"<p>Current Time: {current_time}</p>", "utf-8"))
    self.wfile.write(bytes(
        "<h1>Please Visit Me On <a href=\"https://twitter.com/DigitalRoverDog\">Twitter</a> For The Currently Implemented Features!!!</h1>",
        "utf-8"))

    self.wfile.write(bytes(load_text_file("rover/server/web/templates/footer.html"), "utf-8"))


def load_file(self, path: str, mime_type: str):
    # HTTP Headers
    self.send_response(200)
    self.send_header("Content-type", mime_type)
    self.end_headers()

    # Load File
    self.wfile.write(load_binary_file(path=path))


def load_text_file(path: str) -> str:
    with open(path, "r") as file:
        file_contents = file.read()
        file.close()

        return file_contents


def load_binary_file(path: str) -> bytes:
    return Path(path).read_bytes()


def load_404_page(self, error_code: int = 404):
    self.send_response(error_code)
    self.send_header("Content-type", "text/html")
    self.end_headers()

    self.wfile.write(bytes(load_text_file("rover/server/web/templates/header.html")
                           .replace("{site_title}", "404 - Page Not Found")
                           .replace("{twitter_title}", "Page Not Found")
                           .replace("{twitter_handle}", config.AUTHOR_TWITTER_HANDLE)
                           .replace("{twitter_description}", "No Page Exists Here")
                           , "utf-8"))

    self.wfile.write(bytes(f"<h1>No Page Found At This Address: {self.path}</h1>", "utf-8"))
    self.wfile.write(bytes(load_text_file("rover/server/web/templates/footer.html"), "utf-8"))


def load_offline_page(self):
    self.send_response(200)
    self.send_header("Content-type", "text/html")
    self.end_headers()

    self.wfile.write(bytes(load_text_file("rover/server/web/templates/header.html")
                           .replace("{site_title}", "Currently Offline")
                           .replace("{twitter_title}", "Currently Offline")
                           .replace("{twitter_handle}", config.AUTHOR_TWITTER_HANDLE)
                           .replace("{twitter_description}", "Cannot Load Page Due Being Offline")
                           , "utf-8"))

    self.wfile.write(bytes(f"<h1>The Current Page Was Not Cached And Cannot Be Loaded Due To Being Offline</h1>", "utf-8"))
    self.wfile.write(bytes(load_text_file("rover/server/web/templates/footer.html"), "utf-8"))
