# Unified HTTP/HTTPS API using http.server and ssl (no external dependencies)
from http.server import BaseHTTPRequestHandler, HTTPServer
import socket
import time
import json
import urllib.request
import ssl
import sys

HOST = "0.0.0.0"
HTTP_PORT = 8080
HTTPS_PORT = 8443
start_time = time.time()

class SimpleHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        print(f"Received GET request: {self.path} from {self.client_address}")
        if self.path == "/":
            print("Responding with 204 No Content for root endpoint")
            self.send_response(204)
            self.end_headers()
        elif self.path == "/health":
            print("Responding with healthcheck")
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"status": "ok"}).encode())
        elif self.path == "/status":
            print("Fetching AWS instance_id and local IP")
            try:
                with urllib.request.urlopen("http://169.254.169.254/latest/meta-data/instance-id", timeout=1) as response:
                    instance_id = response.read().decode()
            except Exception as e:
                print(f"Error fetching instance_id: {e}")
                instance_id = "not available"
            try:
                local_ip = socket.gethostbyname(socket.gethostname())
            except Exception as e:
                print(f"Error fetching local IP: {e}")
                local_ip = "not available"
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"instance_id": instance_id, "local_ip": local_ip}).encode())
        elif self.path == "/uptime":
            uptime_seconds = int(time.time() - start_time)
            print(f"Reporting uptime: {uptime_seconds} seconds")
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"uptime_seconds": uptime_seconds}).encode())
        else:
            print(f"404 Not Found: {self.path}")
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        print(f"Server log: {format % args}")

if __name__ == "__main__":
    mode = "http"
    if len(sys.argv) > 1:
        mode = sys.argv[1].lower()
    if mode == "https":
        port = HTTPS_PORT
        print(f"Starting HTTPS server on {HOST}:{port}")
        httpd = HTTPServer((HOST, port), SimpleHandler)
        # Generate a self-signed certificate if you don't have one:
        # openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -days 365 -nodes
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        context.load_cert_chain(certfile="cert.pem", keyfile="key.pem")
        httpd.socket = context.wrap_socket(httpd.socket, server_side=True)
        httpd.serve_forever()
    else:
        port = HTTP_PORT
        print(f"Starting HTTP server on {HOST}:{port}")
        httpd = HTTPServer((HOST, port), SimpleHandler)
        httpd.serve_forever()
