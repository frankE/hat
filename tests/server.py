#!/usr/bin/env python3
from http.server import BaseHTTPRequestHandler
from http.server import HTTPServer
import json

test_json = {
    "id": 1,
    "name": "test",
    "attributes": {
        "attribute1": "value1",
        "attribute2": "value2",
    }
}
host_name = "localhost"
server_port = 8080


class TestRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "application/json")
        self.end_headers()
        self.wfile.write(bytes(json.dumps(test_json), "utf-8"))
        self.wfile.flush()

    def do_POST(self):
        length = self.headers['Content-Length']
        body = self.rfile.read(int(length))
        self.send_response(201)
        self.end_headers()
        self.wfile.write(body)
        self.wfile.flush()


class WebServer():
    def __init__(self, host_name, server_port):
        self.web_server = HTTPServer((host_name, server_port), TestRequestHandler)

    def start_server(self):
        self.web_server.serve_forever()

    def stop_server(self):
        self.web_server.server_close()


if __name__ == "__main__":
    webserver = WebServer(host_name, server_port)
    webserver.start_server()
