"""
CyberLab Pro v3.0 — Password Cracker (Android/Chaquopy)
"""
import os
import re
import subprocess
from pathlib import Path
from core.utils import run_command, get_tool_path, check_tool, DATA_DIR, WORDLIST_DIR


class PasswordCracker:
    def __init__(self):
        self.hash_file = None
        self.results = []

    def identify_hash(self, hash_value: str) -> dict:
        patterns = [
            (r"^\$2[ayb]\$", "bcrypt", 3200),
            (r"^\$6\$", "sha512", 1800),
            (r"^\$1\$", "md5", 500),
            (r"^\$5\$", "sha256", 7400),
            (r"^[a-f0-9]{32}$", "md5", 0),
            (r"^[a-f0-9]{40}$", "sha1", 100),
            (r"^[a-f0-9]{64}$", "sha256", 1400),
            (r"^[a-f0-9]{128}$", "sha512", 1700),
        ]
        for pattern, name, mode in patterns:
            if re.match(pattern, hash_value, re.IGNORECASE):
                return {"type": name, "mode": mode}
        return {"type": "unknown", "mode": 0}

    def crack(self, hash_value: str = None, hash_file: str = None,
              wordlist: str = None, tool: str = "hashcat",
              hash_mode: str = "22000", use_rules: bool = False) -> dict:
        wl = wordlist or f"{WORDLIST_DIR}/rockyou.txt"
        if not os.path.isabs(wl):
            wl = f"{WORDLIST_DIR}/{wl}"

        if hash_file:
            target = hash_file
        elif hash_value:
            target = f"/tmp/hash_{hash_value[:8]}.txt"
            with open(target, "w") as f:
                f.write(hash_value + "\n")
        else:
            return {"success": False, "error": "No hash provided"}

        if tool == "hashcat" and check_tool("hashcat"):
            cmd = f"{get_tool_path('hashcat')} -m {hash_mode} -a 0 {target} {wl} --force -O --status"
            if use_rules:
                cmd += f" -r {WORDLIST_DIR}/best64.rule"
        elif tool == "john" and check_tool("john"):
            cmd = f"{get_tool_path('john')} --wordlist={wl} {target}"
        else:
            return {"success": False, "error": f"Tool {tool} not available"}

        res = run_command(cmd, timeout=600)
        if res["success"]:
            m = re.search(r"[A-Za-z0-9!@#$%^&*()_+\-=\[\]{};':\"\\|,.<>\/?]{4,}", res["stdout"])
            if m:
                return {"success": True, "password": m.group(0), "output": res["stdout"]}
        return {"success": False, "output": res.get("stdout", "")[:500]}

    def generate_wordlist(self, min_len: int, max_len: int, charset: str = None, output: str = None) -> dict:
        out = output or f"{WORDLIST_DIR}/custom_{int(__import__('time').time())}.txt"
        cmd = f"{get_tool_path('crunch')} {min_len} {max_len}"
        if charset:
            cmd += f" {charset}"
        cmd += f" -o {out}"
        res = run_command(cmd, timeout=120)
        return {"success": res["success"], "file": out}
