import json
import os
import time
import urllib.request
from http.server import BaseHTTPRequestHandler, HTTPServer


HEALTH_URL = os.getenv(
    "HEALTH_URL",
    "http://backend:5000/api/health"
)

PORT = int(
    os.getenv("PORT", "8000")
)


def check_flask():
    start_time = time.perf_counter()

    try:
        with urllib.request.urlopen(
            HEALTH_URL,
            timeout=5
        ) as response:

            response_body = response.read()
            response_code = response.status

            elapsed = (
                time.perf_counter() -
                start_time
            )

            data = json.loads(
                response_body.decode("utf-8")
            )

            is_healthy = (
                response_code == 200
                and data.get("status") == "ok"
            )

            return {
                "up": 1 if is_healthy else 0,
                "response_code": response_code,
                "latency": elapsed,
            }

    except Exception:
        elapsed = (
            time.perf_counter() -
            start_time
        )

        return {
            "up": 0,
            "response_code": 0,
            "latency": elapsed,
        }


class MetricsHandler(BaseHTTPRequestHandler):

    def do_GET(self):

        if self.path != "/metrics":
            self.send_response(404)
            self.end_headers()
            return

        result = check_flask()

        metrics = f"""# HELP company_flask_up Whether the Flask application is healthy.
# TYPE company_flask_up gauge
company_flask_up {result["up"]}

# HELP company_flask_http_status HTTP status code returned by Flask.
# TYPE company_flask_http_status gauge
company_flask_http_status {result["response_code"]}

# HELP company_flask_response_time_seconds Flask health response time.
# TYPE company_flask_response_time_seconds gauge
company_flask_response_time_seconds {result["latency"]:.6f}
"""

        body = metrics.encode("utf-8")

        self.send_response(200)
        self.send_header(
            "Content-Type",
            "text/plain; version=0.0.4"
        )
        self.send_header(
            "Content-Length",
            str(len(body))
        )
        self.end_headers()

        self.wfile.write(body)

    def log_message(self, format, *args):
        return


if __name__ == "__main__":

    print(
        "OrtakPortal Exporter başlatıldı."
    )

    print(
        f"Health URL: {HEALTH_URL}"
    )

    print(
        f"Metrics port: {PORT}"
    )

    server = HTTPServer(
        ("0.0.0.0", PORT),
        MetricsHandler
    )

    server.serve_forever()