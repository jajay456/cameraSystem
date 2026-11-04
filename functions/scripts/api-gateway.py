#!/usr/bin/env python3
import http.client
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[2] / ".env")

API_KEY = os.environ.get("API_KEY")
UPSTREAM_HOST = "127.0.0.1"
UPSTREAM_PORT = int(os.environ.get("UPSTREAM_PORT", "8000"))
LISTEN_PORT = int(os.environ.get("API_PORT", "8001"))


class Gateway(BaseHTTPRequestHandler):
    def do_GET(self):
        self.forward()

    def do_POST(self):
        self.forward()

    def forward(self):
        if not API_KEY or self.headers.get("x-api-key") != API_KEY:
            self.send_json(401, b'{"error":"A valid test API key is required"}')
            return
        path = urlsplit(self.path).path
        marker = "/api/"
        index = path.rfind(marker)
        if index < 0:
            self.send_json(404, b'{"error":"Only /api endpoints are exposed"}')
            return
        upstream_path = path[index:] + (f"?{urlsplit(self.path).query}" if urlsplit(self.path).query else "")
        body = self.rfile.read(int(self.headers.get("content-length", "0")))
        connection = http.client.HTTPConnection(UPSTREAM_HOST, UPSTREAM_PORT, timeout=60)
        try:
            connection.request(self.command, upstream_path, body=body, headers={
                "Content-Type": self.headers.get("content-type", "application/json"),
            })
            response = connection.getresponse()
            payload = response.read()
            self.send_response(response.status)
            self.send_header("Content-Type", response.getheader("Content-Type", "application/json"))
            self.end_headers()
            self.wfile.write(payload)
        finally:
            connection.close()

    def send_json(self, status, payload):
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(payload)

    def log_message(self, format, *args):
        print(format % args)


if __name__ == "__main__":
    if not API_KEY:
        raise SystemExit("API_KEY is required")
    print(f"API-only gateway listening on 127.0.0.1:{LISTEN_PORT}; upstream is 127.0.0.1:{UPSTREAM_PORT}")
    ThreadingHTTPServer(("127.0.0.1", LISTEN_PORT), Gateway).serve_forever()
