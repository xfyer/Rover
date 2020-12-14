#!/usr/bin/python

from datetime import datetime
from pathlib import Path

import pytz

from rover import config


def load_page(self, page: str):
    # Site Data
    site_title: str = "Rover"

    # Twitter Metadata
    twitter_title: str = site_title
    twitter_description: str = "Future Analysis Website Here!!!"

    # HTTP Headers
    self.send_response(200)
    self.send_header("Content-type", "text/html")
    self.end_headers()

    # Header
    write_header(self=self, site_title=site_title, twitter_title=twitter_title, twitter_description=twitter_description)

    # Body
    write_body(self=self, page=page)

    # Footer
    write_footer(self=self)


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

    # Header
    write_header(self=self, site_title="404 - Page Not Found", twitter_title="Page Not Found", twitter_description="No Page Exists Here")

    # 404 Page Body - TODO: Add In Optional Variable Substitution Via write_body(...)
    self.wfile.write(bytes(load_text_file("rover/server/web/pages/errors/404.html").replace("{path}", self.path), "utf-8"))

    # Footer
    write_footer(self=self)


def load_offline_page(self):
    self.send_response(200)
    self.send_header("Content-type", "text/html")
    self.end_headers()

    title = "Currently Offline"
    description = "Cannot Load Page Due Being Offline"

    # Header
    write_header(self=self, site_title=title, twitter_title=title, twitter_description=description)

    # Body
    write_body(self=self, page='errors/offline')

    # Footer
    write_footer(self=self)


def write_header(self, site_title: str, twitter_title: str, twitter_description: str):
    current_time: str = f"{datetime.now().astimezone(tz=pytz.UTC):%A, %B, %d %Y at %H:%M:%S.%f %z}"

    self.wfile.write(bytes(load_text_file("rover/server/web/templates/header.html")
                           .replace("{site_title}", site_title)
                           .replace("{twitter_title}", twitter_title)
                           .replace("{twitter_handle}", config.AUTHOR_TWITTER_HANDLE)
                           .replace("{twitter_description}", twitter_description)
                           .replace("{current_time}", current_time)
                           , "utf-8"))


def write_body(self, page: str):
    self.wfile.write(bytes(load_text_file(f"rover/server/web/pages/{page}.html"), "utf-8"))


def write_footer(self):
    self.wfile.write(bytes(load_text_file("rover/server/web/templates/footer.html"), "utf-8"))
