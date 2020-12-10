#!/usr/bin/python

def handle_api(self):
    self.send_response(200)
    self.send_header("Content-type", "application/json")
    self.end_headers()

    self.wfile.write(bytes("{}", "utf-8"))
