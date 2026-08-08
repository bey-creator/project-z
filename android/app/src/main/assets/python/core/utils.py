"""
CyberLab Pro v3.0 — Android Core Utilities
Ported from Flask/Termux version for Chaquopy Android runtime.
"""
import os
import re
import json
import time
import signal
import subprocess
import threading
from pathlib import Path
from queue import Queue, Empty
from datetime import datetime

# Android paths (set by Chaquopy bridge at runtime)
BASE_DIR = os.environ.get("CYBERLAB_BASE_DIR", "/data/data/com.cyberlab/files")
DATA_DIR = os.path.join(BASE_DIR, "cyberlab-data")
CAPTURE_DIR = os.path.join(DATA_DIR, "captures")
WORDLIST_DIR = os.path.join(DATA_DIR, "wordlists")
BINARIES_DIR = os.path.join(BASE_DIR, "binaries")
LOG_DIR = os.path.join(DATA_DIR, "logs")
CONFIG_DIR = os.path.join(DATA_DIR, "app/config")
MANIFEST_PATH = os.path.join(BASE_DIR, "tools_manifest.json")

for d in [DATA_DIR, CAPTURE_DIR, WORDLIST_DIR, LOG_DIR, CONFIG_DIR]:
    Path(d).mkdir(parents=True, exist_ok=True)


def is_rooted() -> bool:
    try:
        result = subprocess.run(["su", "-c", "id"], capture_output=True, timeout=3)
        return result.returncode == 0
    except Exception:
        return False


def run_command(cmd, timeout: int = 300, shell: bool = False) -> dict:
    """Execute a command and return structured result."""
    try:
        if isinstance(cmd, str) and not shell:
            import shlex
            cmd = shlex.split(cmd)
        proc = subprocess.Popen(
            cmd, shell=shell,
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
            preexec_fn=os.setsid if hasattr(os, "setsid") else None,
        )
        stdout, _ = proc.communicate(timeout=timeout)
        return {
            "success": proc.returncode == 0,
            "returncode": proc.returncode,
            "stdout": stdout,
            "command": str(cmd),
        }
    except subprocess.TimeoutExpired:
        proc.kill()
        return {"success": False, "error": "timeout", "stdout": ""}
    except Exception as e:
        return {"success": False, "error": str(e), "stdout": ""}


def get_tool_path(name: str) -> str:
    """Resolve tool path from manifest or binaries dir."""
    try:
        with open(MANIFEST_PATH) as f:
            manifest = json.load(f)
        tool_info = manifest.get("tools", {}).get(name, {})
        rel = tool_info.get("path", f"binaries/{name}")
        if tool_info.get("type") == "native_binary":
            return os.path.join(BINARIES_DIR, rel)
        return os.path.join(BASE_DIR, rel)
    except Exception:
        return os.path.join(BINARIES_DIR, name)


def check_tool(name: str) -> bool:
    path = get_tool_path(name)
    if os.path.exists(path):
        return os.access(path, os.X_OK) or path.endswith(".py")
    return subprocess.run(["which", name], capture_output=True).returncode == 0


def detect_interfaces() -> list:
    """Auto-detect wireless interfaces via /sys/class/net."""
    interfaces = []
    net_path = "/sys/class/net"
    if not os.path.exists(net_path):
        return interfaces
    for iface_name in os.listdir(net_path):
        if iface_name == "lo":
            continue
        is_wireless = (
            os.path.exists(f"{net_path}/{iface_name}/wireless") or
            os.path.exists(f"{net_path}/{iface_name}/phy80211")
        )
        if not is_wireless:
            continue
        iface_info = {
            "name": iface_name,
            "type": "USB Adapter" if os.path.exists(f"{net_path}/{iface_name}/device/driver") else "Built-in",
            "chipset": "unknown",
            "driver": "unknown",
            "monitor_support": False,
            "recommended": False,
            "warning": None,
        }
        # Detect driver
        usb_path = f"{net_path}/{iface_name}/device/driver"
        if os.path.exists(usb_path):
            try:
                driver_link = os.readlink(usb_path)
                driver = driver_link.split("/")[-1]
                iface_info["driver"] = driver
                good = ["ath9k_htc", "rt2800usb", "rtl8187", "rtl8188eus",
                        "rtl8812au", "rtl8814au", "mt76x0u", "mt76x2u"]
                if any(g in driver.lower() for g in good):
                    iface_info["monitor_support"] = True
                    iface_info["recommended"] = True
            except Exception:
                pass
        # Check monitor capability via iw
        try:
            res = subprocess.run(
                ["iw", "dev", iface_name, "info"],
                capture_output=True, text=True, timeout=5
            )
            if "monitor" in res.stdout.lower():
                iface_info["monitor_support"] = True
        except Exception:
            pass
        if iface_info["type"] == "Built-in" and not iface_info["monitor_support"]:
            iface_info["warning"] = "Built-in WiFi - monitor mode unlikely"
        interfaces.append(iface_info)
    interfaces.sort(key=lambda x: (not x["recommended"], x["name"]))
    return interfaces


def get_default_gateway() -> dict:
    """Auto-detect default gateway (router) IP and interface."""
    try:
        with open("/proc/net/route") as f:
            for line in f.readlines()[1:]:
                parts = line.strip().split()
                if len(parts) >= 4 and parts[1] == "00000000" and parts[2] != "00000000":
                    gw_hex = parts[2]
                    gw = ".".join(str(int(gw_hex[i:i+2], 16)) for i in (6, 4, 2, 0))
                    return {"gateway": gw, "interface": parts[0]}
    except Exception:
        pass
    res = run_command("ip route show default", timeout=10)
    if res["success"]:
        m = re.search(r"default via (\d+\.\d+\.\d+\.\d+)\s+dev\s+(\S+)", res["stdout"])
        if m:
            return {"gateway": m.group(1), "interface": m.group(2)}
    gw_info = get_default_gateway()
    if not gw_info.get("gateway"):
        base = ".".join(gw_info.get("gateway", "192.168.1.1").split(".")[:3])
        return f"{base}.0/24"
    return None


def log_activity(action: str, target: str, status: str = "success"):
    entry = {
        "timestamp": datetime.now().isoformat(),
        "action": action,
        "target": target,
        "status": status,
    }
    log_file = os.path.join(LOG_DIR, "activity.log")
    try:
        with open(log_file, "a") as f:
            f.write(json.dumps(entry) + "\n")
    except Exception:
        pass


class CommandRunner:
    """Background command runner with output queue."""
    def __init__(self):
        self._processes = {}
        self._queues = {}
        self._threads = {}

    def start(self, cmd_id: str, cmd: list, callback=None):
        def _run():
            try:
                proc = subprocess.Popen(
                    cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True
                )
                self._processes[cmd_id] = proc
                for line in iter(proc.stdout.readline, ""):
                    if not line:
                        break
                    if callback:
                        callback(line.strip())
                proc.wait()
            except Exception as e:
                if callback:
                    callback(f"[ERROR] {e}")
            finally:
                self._processes.pop(cmd_id, None)

        t = threading.Thread(target=_run, daemon=True)
        t.start()
        self._threads[cmd_id] = t

    def stop(self, cmd_id: str):
        proc = self._processes.pop(cmd_id, None)
        if proc and proc.poll() is None:
            try:
                if hasattr(os, "killpg"):
                    os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
                else:
                    proc.terminate()
                proc.wait(timeout=5)
            except Exception:
                try:
                    proc.kill()
                except Exception:
                    pass

    def stop_all(self):
        for cmd_id in list(self._processes.keys()):
            self.stop(cmd_id)
