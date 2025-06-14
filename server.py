# Unified HTTP/HTTPS API using http.server and ssl (no external dependencies)
from http.server import BaseHTTPRequestHandler, HTTPServer
import socket
import time
import json
import urllib.request
import ssl
import sys

HOST = "0.0.0.0"
HTTP_PORT = 80
HTTPS_PORT = 443
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
            response = json.dumps({"status": "ok"}).encode()
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Content-Length', str(len(response)))
            self.end_headers()
            self.wfile.write(response)
        elif self.path == "/status":
            print("Fetching AWS instance_id and local IP (IMDSv2)")
            instance_id = "not available"
            try:
                # Step 1: Get IMDSv2 token
                req_token = urllib.request.Request(
                    "http://169.254.169.254/latest/api/token",
                    method="PUT",
                    headers={"X-aws-ec2-metadata-token-ttl-seconds": "21600"}
                )
                with urllib.request.urlopen(req_token, timeout=1) as token_response:
                    token = token_response.read().decode()
                # Step 2: Use token to get instance-id
                req_id = urllib.request.Request(
                    "http://169.254.169.254/latest/meta-data/instance-id",
                    headers={"X-aws-ec2-metadata-token": token}
                )
                with urllib.request.urlopen(req_id, timeout=1) as response_id:
                    instance_id = response_id.read().decode()
            except Exception as e:
                print(f"Error fetching instance_id (IMDSv2): {e}")
                instance_id = "not available"
            try:
                local_ip = socket.gethostbyname(socket.gethostname())
            except Exception as e:
                print(f"Error fetching local IP: {e}")
                local_ip = "not available"
            response = json.dumps({"instance_id": instance_id, "local_ip": local_ip}).encode()
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Content-Length', str(len(response)))
            self.end_headers()
            self.wfile.write(response)
        elif self.path == "/uptime":
            uptime_seconds = int(time.time() - start_time)
            print(f"Reporting uptime: {uptime_seconds} seconds")
            response = json.dumps({"uptime_seconds": uptime_seconds}).encode()
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Content-Length', str(len(response)))
            self.end_headers()
            self.wfile.write(response)
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
        context.load_cert_chain(certfile="/srv/cert.pem", keyfile="/srv/key.pem")
        httpd.socket = context.wrap_socket(httpd.socket, server_side=True)
        httpd.serve_forever()
    else:
        port = HTTP_PORT
        print(f"Starting HTTP server on {HOST}:{port}")
        httpd = HTTPServer((HOST, port), SimpleHandler)
        httpd.serve_forever()
