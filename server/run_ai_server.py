#!/usr/bin/env python3
"""
BS LAB TOOL™ - AI Central Server Master Runner
==============================================
Runs the background Log Ingestion Daemon and serves OTA updates over local/LAN HTTP.
Can be run on workshop server or technician primary PC.
"""

import os
import sys
import time
import json
import threading
import http.server
import socketserver
from pathlib import Path
from datetime import datetime

SERVER_DIR = Path(__file__).resolve().parent
ROOT_DIR = SERVER_DIR.parent
OTA_DIR = ROOT_DIR / "resources" / "ota"
PORT = 8080

from log_watcher_daemon import LogIngestionDaemon, log_activity

class OtaHttpHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(OTA_DIR), **kwargs)

    def end_headers(self):
        # Enable CORS and disable caching for instant updates
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
        super().end_headers()

    def log_message(self, format, *args):
        # Suppress verbose standard HTTP access logs
        pass

def run_http_server(port: int = PORT):
    try:
        with socketserver.TCPServer(("", port), OtaHttpHandler) as httpd:
            log_activity(f"[+] 🌐 Local OTA Distribution Server listening on http://127.0.0.1:{port}/")
            httpd.serve_forever()
    except Exception as e:
        log_activity(f"[-] HTTP Server notice: Port {port} already bound or error: {e}")

def main():
    print("=" * 66)
    print("⚡ BS LAB TOOL™ - AI AUTONOMOUS SELF-UPDATING SERVER ENGINE")
    print("👤 Registered to : Syed Bisharat Ali (Shah Ji) | Arif Center, Lahore")
    print(f"⏰ Server Time   : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 66)

    # 1. Start HTTP Server in background thread
    http_thread = threading.Thread(target=run_http_server, daemon=True)
    http_thread.start()

    # 2. Run Log Ingestion Daemon
    daemon = LogIngestionDaemon()
    daemon.run_daemon(poll_interval=5)

if __name__ == "__main__":
    main()
