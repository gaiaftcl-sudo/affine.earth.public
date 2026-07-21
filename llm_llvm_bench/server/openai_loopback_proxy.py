"""Transparent loopback proxy for a live OpenAI-compatible upstream."""

from __future__ import annotations

import argparse
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


class ProxyHandler(BaseHTTPRequestHandler):
    upstream_base_url = ""

    def log_message(self, message: str, *args: object) -> None:
        print(f"{self.client_address[0]} {message % args}")

    def _proxy(self) -> None:
        content_length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(content_length) if content_length else None
        headers = {
            key: value
            for key, value in self.headers.items()
            if key.lower() not in {"host", "content-length", "connection"}
        }
        request = Request(
            f"{self.upstream_base_url}{self.path}",
            data=body,
            headers=headers,
            method=self.command,
        )
        try:
            with urlopen(request, timeout=610) as response:
                self._write_response(response.status, response.headers.items(), response.read())
        except HTTPError as error:
            self._write_response(error.code, error.headers.items(), error.read())
        except URLError as error:
            encoded = f'{{"error":{{"message":"upstream unavailable: {error.reason}"}}}}'.encode()
            self._write_response(502, (("Content-Type", "application/json"),), encoded)

    def _write_response(self, status: int, headers: object, body: bytes) -> None:
        self.send_response(status)
        for key, value in headers:
            if key.lower() not in {"connection", "transfer-encoding", "content-length"}:
                self.send_header(key, value)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    do_GET = _proxy
    do_POST = _proxy


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=8080)
    parser.add_argument(
        "--upstream",
        default=os.environ.get("OPENAI_LOOPBACK_UPSTREAM", "http://127.0.0.1:1234"),
        help="Live upstream URL, without a trailing slash.",
    )
    args = parser.parse_args()
    ProxyHandler.upstream_base_url = args.upstream.rstrip("/")
    server = ThreadingHTTPServer(("127.0.0.1", args.port), ProxyHandler)
    print(f"Forwarding http://127.0.0.1:{args.port} to {ProxyHandler.upstream_base_url}")
    server.serve_forever()


if __name__ == "__main__":
    main()
