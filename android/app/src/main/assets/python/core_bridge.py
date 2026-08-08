"""
CyberLab Pro v3.0 — Chaquopy Python Bridge
Executes tool commands inside the Android APK via embedded Python 3.11.
React Native calls into this through the Chaquopy interface.
"""
import os
import sys
import json
import subprocess
import threading
from pathlib import Path

# Android app private storage (set by Chaquopy at runtime)
BASE_DIR = os.environ.get("CYBERLAB_BASE_DIR", "/data/data/com.cyberlab/files")
DATA_DIR = os.path.join(BASE_DIR, "cyberlab-data")
CAPTURE_DIR = os.path.join(DATA_DIR, "captures")
WORDLIST_DIR = os.path.join(DATA_DIR, "wordlists")
LOG_DIR = os.path.join(DATA_DIR, "logs")
MANIFEST_PATH = os.path.join(BASE_DIR, "tools_manifest.json")

# Binaries bundled in APK assets, extracted at first launch
BINARIES_DIR = os.path.join(BASE_DIR, "binaries")

for d in [DATA_DIR, CAPTURE_DIR, WORDLIST_DIR, LOG_DIR]:
    Path(d).mkdir(parents=True, exist_ok=True)


def load_manifest() -> dict:
    try:
        with open(MANIFEST_PATH) as f:
            return json.load(f)
    except Exception:
        return {"tools": {}, "categories": {}}


MANIFEST = load_manifest()


def is_rooted() -> bool:
    try:
        result = subprocess.run(
            ["su", "-c", "id"],
            capture_output=True, timeout=3
        )
        return result.returncode == 0
    except Exception:
        return False


def run_command(cmd: str, timeout: int = 300, shell: bool = False) -> dict:
    """Run a system command and return structured output."""
    try:
        if isinstance(cmd, str) and not shell:
            cmd = cmd.split()
        proc = subprocess.Popen(
            cmd,
            shell=shell,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            preexec_fn=os.setsid if hasattr(os, "setsid") else None,
        )
        stdout, _ = proc.communicate(timeout=timeout)
        return {
            "success": proc.returncode == 0,
            "returncode": proc.returncode,
            "stdout": stdout,
            "command": cmd if isinstance(cmd, str) else " ".join(cmd),
        }
    except subprocess.TimeoutExpired:
        proc.kill()
        return {"success": False, "error": "timeout", "stdout": "", "command": cmd}
    except Exception as e:
        return {"success": False, "error": str(e), "stdout": "", "command": cmd}


def get_tool_path(tool_name: str) -> str:
    """Resolve full path to a tool binary or script."""
    tool_info = MANIFEST.get("tools", {}).get(tool_name, {})
    tool_type = tool_info.get("type", "native_binary")
    rel_path = tool_info.get("path", tool_name)
    if tool_type == "native_binary":
        return os.path.join(BINARIES_DIR, rel_path)
    return os.path.join(BASE_DIR, rel_path)


def check_tool_available(tool_name: str) -> bool:
    """Check if a tool exists and is executable."""
    path = get_tool_path(tool_name)
    if os.path.exists(path):
        return os.access(path, os.X_OK) or path.endswith(".py")
    # Also check system PATH
    return subprocess.run(
        ["which", tool_name], capture_output=True
    ).returncode == 0


def get_available_tools() -> list:
    """Return list of tools that are available on this device."""
    available = []
    for name, info in MANIFEST.get("tools", {}).items():
        if check_tool_available(name):
            available.append({
                "name": name,
                "category": info.get("category", "unknown"),
                "needs_root": info.get("needs_root", False),
                "available": True,
            })
    return available


def execute_tool(tool_name: str, args: dict) -> dict:
    """Execute a tool with given arguments."""
    tool_info = MANIFEST.get("tools", {}).get(tool_name)
    if not tool_info:
        return {"success": False, "error": f"unknown_tool: {tool_name}"}

    needs_root = tool_info.get("needs_root", False)
    if needs_root and not is_rooted():
        return {"success": False, "error": "root_required"}

    tool_path = get_tool_path(tool_name)
    tool_type = tool_info.get("type", "native_binary")

    if tool_type == "native_binary":
        cmd = [tool_path] + _build_args(tool_name, args)
    else:
        # Python module
        cmd = [sys.executable, tool_path] + _build_args(tool_name, args)

    timeout = args.get("timeout", 300)
    return run_command(cmd, timeout=timeout)


def _build_args(tool_name: str, args: dict) -> list:
    """Convert args dict to CLI argument list based on tool."""
    argv = []
    # Common patterns
    if "target" in args:
        argv += ["-t", args["target"]]
    if "port" in args:
        argv += ["-p", str(args["port"])]
    if "interface" in args:
        argv += ["-i", args["interface"]]
    if "output" in args:
        argv += ["-o", args["output"]]
    if "wordlist" in args:
        wl = args["wordlist"]
        if not os.path.isabs(wl):
            wl = os.path.join(WORDLIST_DIR, wl)
        argv += ["-w", wl]
    if "threads" in args:
        argv += ["--threads", str(args["threads"])]
    if "timeout" in args and tool_name not in ("nmap",):
        argv += ["--timeout", str(args["timeout"])]
    if args.get("verbose"):
        argv.append("-v")
    if args.get("aggressive"):
        argv.append("-A")
    return argv


def get_status() -> dict:
    """Get full system status for the dashboard."""
    rooted = is_rooted()
    return {
        "version": "3.0.0",
        "platform": "Android",
        "rooted": rooted,
        "binaries_dir": BINARIES_DIR,
        "data_dir": DATA_DIR,
        "total_tools": len(MANIFEST.get("tools", {})),
        "available_tools": len(get_available_tools()),
        "categories": list(MANIFEST.get("categories", {}).keys()),
    }
