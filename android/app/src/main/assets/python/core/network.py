"""
CyberLab Pro v3.0 — Network Lab (Android/Chaquopy)
"""
import os
import re
import json
import time
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path
from core.utils import run_command, get_tool_path, check_tool, DATA_DIR, CAPTURE_DIR


class NetworkLab:
    def __init__(self):
        self.scan_results = []
        self.hosts = []

    def scan_network(self, network_range: str, ports: str = None, scan_type: str = "quick") -> list:
        if scan_type == "quick":
            cmd = f"{get_tool_path('nmap')} -sn {network_range} -oX -"
        elif scan_type == "service":
            port_arg = f"-p {ports}" if ports else "-p-"
            cmd = f"{get_tool_path('nmap')} -sV {port_arg} {network_range} -oX -"
        elif scan_type == "aggressive":
            cmd = f"{get_tool_path('nmap')} -A {network_range} -oX -"
        else:
            cmd = f"{get_tool_path('nmap')} -sn {network_range} -oX -"
        res = run_command(cmd, timeout=300)
        if not res["success"]:
            return []
        hosts = self._parse_nmap_xml(res["stdout"])
        self.hosts = hosts
        return hosts

    def _parse_nmap_xml(self, xml_output: str) -> list:
        hosts = []
        try:
            root = ET.fromstring(xml_output)
            for host in root.findall(".//host"):
                addr = host.find("address")
                ip = addr.get("addr") if addr is not None else "0.0.0.0"
                status = host.find("status")
                state = status.get("state", "down") if status is not None else "down"
                ports_list = []
                for port in host.findall(".//port"):
                    port_id = port.get("portid", "")
                    service = port.find("service")
                    service_name = service.get("name", "unknown") if service is not None else "unknown"
                    state_elem = port.find("state")
                    port_state = state_elem.get("state", "closed") if state_elem is not None else "closed"
                    ports_list.append({"port": port_id, "service": service_name, "state": port_state})
                hosts.append({"ip": ip, "state": state, "ports": ports_list})
        except ET.ParseError:
            pass
        return hosts

    def discover_cctv(self, network_range: str) -> list:
        cctv_ports = "80,554,8080,37777,8000,8899,8554"
        cmd = f"{get_tool_path('nmap')} -p {cctv_ports} --open -sV -oX - {network_range}"
        res = run_command(cmd, timeout=120)
        hosts = self._parse_nmap_xml(res["stdout"]) if res["success"] else []
        cctv_devices = []
        for host in hosts:
            has_rtsp = any(p["port"] == "554" for p in host.get("ports", []))
            has_http = any(p["port"] in ("80", "8080", "8000") for p in host.get("ports", []))
            if has_rtsp or has_http:
                cctv_devices.append({
                    "ip": host["ip"], "ports": host["ports"],
                    "has_rtsp": has_rtsp,
                    "urls": {"rtsp": f"rtsp://admin:admin@{host['ip']}:554/stream1",
                             "http": f"http://{host['ip']}:80"},
                })
        return cctv_devices

    def quick_port_scan(self, ip: str) -> list:
        common = "21,22,23,25,53,80,110,139,143,443,445,554,993,995,3306,3389,5432,5900,8000,8080,8443"
        cmd = f"{get_tool_path('nmap')} -p {common} --open -sV {ip} -oX -"
        res = run_command(cmd, timeout=60)
        hosts = self._parse_nmap_xml(res["stdout"]) if res["success"] else []
        return hosts[0]["ports"] if hosts else []

    def ping_sweep(self, network_range: str) -> list:
        res = run_command(f"{get_tool_path('nmap')} -sn -n {network_range}")
        return re.findall(r"(\d+\.\d+\.\d+\.\d+)", res["stdout"]) if res["success"] else []

    def get_local_subnet(self, interface: str = None) -> str:
        res = run_command("ip addr show" + (f" {interface}" if interface else ""), timeout=10)
        if res["success"]:
            m = re.search(r"inet (\d+\.\d+\.\d+\.\d+/\d+)", res["stdout"])
            if m:
                return m.group(1)
        return "192.168.1.0/24"
