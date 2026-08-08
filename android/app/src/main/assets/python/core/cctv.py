"""
CyberLab Pro v3.0 — CCTV Lab (Android/Chaquopy)
"""
import os
import re
import time
import subprocess
from pathlib import Path
from core.utils import run_command, get_tool_path, check_tool, DATA_DIR, CAPTURE_DIR

SNAPSHOT_DIR = f"{CAPTURE_DIR}/snapshots"
Path(SNAPSHOT_DIR).mkdir(parents=True, exist_ok=True)


class CCTVLab:
    def __init__(self):
        self.devices = []
        self.current_stream = None

    def scan_network(self, network_range: str) -> list:
        cmd = f"{get_tool_path('nmap')} -p 80,554,8080,37777,8000,8899,8554 --open -sV -oX - {network_range}"
        res = run_command(cmd, timeout=120)
        if not res["success"]:
            return []
        devices = self._parse_for_cctv(res["stdout"])
        self.devices = devices
        return devices

    def _parse_for_cctv(self, xml_output: str) -> list:
        import xml.etree.ElementTree as ET
        devices = []
        try:
            root = ET.fromstring(xml_output)
            for host in root.findall(".//host"):
                addr = host.find("address")
                ip = addr.get("addr") if addr is not None else "0.0.0.0"
                ports = []
                for port in host.findall(".//port"):
                    port_id = port.get("portid", "")
                    service = port.find("service")
                    svc_name = service.get("name", "unknown") if service is not None else "unknown"
                    ports.append({"port": port_id, "service": svc_name})
                has_rtsp = any(p["port"] in ("554", "8554") for p in ports)
                has_http = any(p["port"] in ("80", "8080", "8000") for p in ports)
                if has_rtsp or has_http:
                    devices.append({
                        "ip": ip, "ports": ports, "has_rtsp": has_rtsp,
                        "urls": {
                            "rtsp": f"rtsp://admin:admin@{ip}:554/stream1",
                            "http": f"http://{ip}:80",
                        },
                    })
        except Exception:
            pass
        return devices

    def detect_local_subnet(self) -> str:
        res = run_command("ip addr show", timeout=10)
        if res["success"]:
            m = re.search(r"inet (\d+\.\d+\.\d+\.\d+/\d+)", res["stdout"])
            if m:
                return m.group(1)
        return "192.168.1.0/24"

    def test_default_credentials(self, ip: str, port: int = 80) -> dict:
        defaults = [("admin", "admin"), ("admin", "12345"), ("admin", "password"),
                    ("root", "root"), ("admin", ""), ("admin", "admin123")]
        results = []
        for user, pwd in defaults:
            res = run_command(
                f"{get_tool_path('curl')} -s --connect-timeout 3 -o /dev/null -w '%{{http_code}}' "
                f"-u {user}:{pwd} http://{ip}:{port}/", timeout=10
            )
            if res["success"] and res["stdout"].strip() == "200":
                results.append({"username": user, "password": pwd})
                break
        return {"success": len(results) > 0, "credentials": results}

    def get_stream_url(self, ip: str, port: int = 554) -> str:
        return f"rtsp://admin:admin@{ip}:{port}/stream1"

    def stop_stream(self) -> dict:
        if self.current_stream:
            try:
                self.current_stream.terminate()
                self.current_stream.wait(timeout=5)
            except Exception:
                pass
            self.current_stream = None
        return {"success": True}
