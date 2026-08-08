"""
CyberLab Pro v3.0 — Python Tool Runner
Only for tools that are NATIVELY Python (not wrappers for binaries).
Runs the actual tool source code via Chaquopy.
"""
import os
import sys
import subprocess
from pathlib import Path

BASE_DIR = os.environ.get("CYBERLAB_BASE_DIR", "/data/data/com.cyberlab/files")
TOOLS_DIR = os.path.join(BASE_DIR, "assets/python/tools_py")
WORDLIST_DIR = os.path.join(BASE_DIR, "assets/wordlists")

# Tools that are natively Python (source code runs via Chaquopy)
PYTHON_TOOLS = {
    "sqlmap": {"module": "sqlmap.sqlmap", "main": "main"},
    "nikto": {"module": "nikto.nikto", "main": "main"},
    "wfuzz": {"module": "wfuzz.__main__", "main": "main"},
    "routersploit": {"module": "routersploit.interpreter", "main": "main"},
    "maigret": {"module": "maigret.maigret", "main": "main"},
    "holehe": {"module": "holehe.core", "main": "main"},
    "photon": {"module": "photon.photon", "main": "main"},
    "instaloader": {"module": "instaloader.__main__", "main": "main"},
    "snscrape": {"module": "snscrape._cli", "main": "main"},
    "h8mail": {"module": "h8mail.main", "main": "main"},
    "osintgram": {"module": "Osintgram.main", "main": "main"},
    "volatility": {"module": "volatility.cli", "main": "main"},
    "hash-identifier": {"module": "hashidentifier", "main": "main"},
    "cewl": {"module": "cewl.cewl", "main": "main"},
    "binwalk": {"module": "binwalk", "main": "main"},
    "wifite": {"module": "wifite.wifite", "main": "main"},
    "airgeddon": {"module": "airgeddon.airgeddon", "main": "main"},
    "phoneinfoga": {"module": "phoneinfoga.main", "main": "main"},
}

def run_python_tool(tool_name: str, args: dict) -> dict:
    """Run a Python-native tool with given arguments."""
    tool_info = PYTHON_TOOLS.get(tool_name)
    if not tool_info:
        return {"success": False, "error": f"Not a Python tool: {tool_name}"}

    try:
        # Build command
        cmd = [sys.executable, "-m", tool_info["module"]]

        # Add tool-specific arguments
        cmd.extend(_build_args(tool_name, args))

        # Run via subprocess
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            cwd=BASE_DIR,
        )
        stdout, _ = proc.communicate(timeout=args.get("timeout", 300))

        return {
            "success": proc.returncode == 0,
            "exitCode": proc.returncode,
            "output": stdout,
            "tool": tool_name,
        }
    except subprocess.TimeoutExpired:
        proc.kill()
        return {"success": False, "error": "timeout", "tool": tool_name}
    except Exception as e:
        return {"success": False, "error": str(e), "tool": tool_name}


def _build_args(tool_name: str, args: dict) -> list:
    """Build CLI arguments for each Python tool."""
    argv = []
    if not args:
        return argv

    if tool_name == "sqlmap":
        if args.get("target"):
            argv.extend(["-u", args["target"]])
        argv.append("--batch")
        argv.append("--random-agent")
        if args.get("dbs"):
            argv.append("--dbs")
        if args.get("tables"):
            argv.append("--tables")
        if args.get("dump"):
            argv.append("--dump")

    elif tool_name == "nikto":
        argv.extend(["-h", args.get("target", "")])
        if args.get("port"):
            argv.extend(["-p", str(args["port"])])

    elif tool_name == "routersploit":
        argv.extend(["-m", "scanners.autopwn", "-t", args.get("target", "")])

    elif tool_name == "maigret":
        argv.append(args.get("target", ""))

    elif tool_name == "holehe":
        argv.append(args.get("target", ""))

    elif tool_name == "hydra":
        if args.get("userlist"):
            argv.extend(["-L", _wl(args["userlist"])])
        if args.get("passlist"):
            argv.extend(["-P", _wl(args["passlist"])])
        if args.get("service"):
            argv.append(args["service"])
        argv.append(args.get("target", ""))

    elif tool_name == "gobuster":
        argv.extend(["dir", "-u", args.get("target", ""), "-w", _wl(args.get("wordlist", "common_100k.txt"))])

    elif tool_name == "ffuf":
        argv.extend(["-u", args.get("target", "") + "/FUZZ", "-w", _wl(args.get("wordlist", "common_100k.txt"))])

    elif tool_name == "apktool":
        argv.append(args.get("action", "d"))
        if args.get("input"):
            argv.append(args["input"])
        if args.get("output"):
            argv.extend(["-o", args["output"]])
        argv.append("-f")

    elif tool_name == "wifite":
        if args.get("interface"):
            argv.extend(["-i", args["interface"]])

    else:
        # Generic: pass through key-value args
        for k, v in args.items():
            if v and k != "timeout":
                argv.append(f"--{k}")
                argv.append(str(v))

    return argv


def _wl(name: str) -> str:
    """Resolve wordlist path."""
    local = os.path.join(WORDLIST_DIR, name)
    if os.path.exists(local):
        return local
    return name


def get_python_tools() -> list:
    """Return list of available Python-native tools."""
    return [
        {"name": name, "category": _get_category(name), "available": True}
        for name in PYTHON_TOOLS.keys()
    ]


def _get_category(name: str) -> str:
    categories = {
        "sqlmap": "web", "nikto": "web", "wfuzz": "web",
        "routersploit": "device",
        "maigret": "osint", "holehe": "osint", "photon": "osint",
        "instaloader": "osint", "snscrape": "osint", "h8mail": "osint",
        "osintgram": "osint", "phoneinfoga": "osint",
        "volatility": "forensic", "binwalk": "forensic",
        "hash-identifier": "password", "cewl": "password",
        "wifite": "wireless", "airgeddon": "wireless",
    }
    return categories.get(name, "other")
