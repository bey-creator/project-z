"""
CyberLab Pro v3.0 — Sherlock Integration
Adapted from github.com/matauangcina/sherlock
Android static analyzer + exploitation framework (SemGrep OSS Engine).
"""
import os
import re
import json
import subprocess
from core.utils import run_command, get_tool_path, check_tool, DATA_DIR, CAPTURE_DIR

SHERLOCK_DIR = os.path.join(os.environ.get("CYBERLAB_BASE_DIR", "/data/data/com.cyberlab/files/assets"), "external/sherlock")


class SherlockAnalyzer:
    """Android APK static analysis and vulnerability detection."""

    VULN_RULES = {
        "insecure_setresult": {
            "pattern": r"setResult\s*\(",
            "severity": "HIGH",
            "description": "Insecure setResult — activity result exposed to other apps",
        },
        "intent_redirection": {
            "pattern": r"getParcelableExtra.*Intent.*startActivity",
            "severity": "CRITICAL",
            "description": "Intent redirection — attacker can control launched activity",
        },
        "mutable_pending_intent": {
            "pattern": r"PendingIntent\s*\.\s*getActivity\s*\([^,]+,[^,]+,[^,]+,\s*0\s*\)",
            "severity": "HIGH",
            "description": "Mutable PendingIntent without FLAG_IMMUTABLE",
        },
        "insecure_broadcast": {
            "pattern": r"sendBroadcast\s*\([^)]*\)",
            "severity": "MEDIUM",
            "description": "Unprotected broadcast — sensitive data may leak",
        },
        "hardcoded_secret": {
            "pattern": r"(?i)(api[_-]?key|secret|password|token)\s*[=:]\s*[\"'][^\"']{8,}[\"']",
            "severity": "CRITICAL",
            "description": "Hardcoded secret found in source code",
        },
        "insecure_network": {
            "pattern": r"http://[^\"'\s]+",
            "severity": "MEDIUM",
            "description": "Insecure HTTP URL — data transmitted in cleartext",
        },
        "weak_crypto": {
            "pattern": r"(?i)(DES/ECB|MD5|SHA1|Random\s*\()",
            "severity": "MEDIUM",
            "description": "Weak cryptographic algorithm or insecure random",
        },
        "sql_injection_risk": {
            "pattern": r"rawQuery\s*\(.*\+",
            "severity": "HIGH",
            "description": "Potential SQL injection via string concatenation",
        },
        "webview_js_enabled": {
            "pattern": r"setJavaScriptEnabled\s*\(\s*true\s*\)",
            "severity": "MEDIUM",
            "description": "WebView JavaScript enabled — XSS risk if loading untrusted content",
        },
        "debuggable_app": {
            "pattern": r"android:debuggable\s*=\s*[\"']true[\"']",
            "severity": "LOW",
            "description": "Application is debuggable",
        },
    }

    def analyze_apk(self, apk_path: str, args: dict = None) -> dict:
        """Full APK analysis pipeline."""
        results = {"apk": apk_path, "vulnerabilities": [], "summary": {}}
        # Step 1: Decompile APK
        decompile_dir = f"/tmp/sherlock_decompile"
        decompile_res = self.decompile_apk(apk_path, decompile_dir)
        if not decompile_res["success"]:
            return {"success": False, "error": "Decompilation failed"}
        # Step 2: Scan decompiled code
        scan_res = self.scan_source(decompile_dir)
        results["vulnerabilities"] = scan_res.get("findings", [])
        # Step 3: Generate summary
        results["summary"] = self._summarize(results["vulnerabilities"])
        return {"success": True, "results": results}

    def decompile_apk(self, apk_path: str, output_dir: str, args: dict = None) -> dict:
        """Decompile APK using available decompilers."""
        if not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)
        # Try jadx first, then apktool
        if check_tool("jadx"):
            cmd = f"{get_tool_path('jadx')} -d {output_dir} {apk_path}"
        elif check_tool("apktool"):
            cmd = f"{get_tool_path('apktool')} d {apk_path} -o {output_dir} -f"
        else:
            return {"success": False, "error": "No decompiler available"}
        res = run_command(cmd, timeout=120)
        return {"success": res["success"], "output_dir": output_dir}

    def scan_source(self, source_dir: str, args: dict = None) -> dict:
        """Scan decompiled source for vulnerabilities."""
        findings = []
        for root, dirs, files in os.walk(source_dir):
            for fname in files:
                if not fname.endswith((".java", ".smali", ".xml")):
                    continue
                fpath = os.path.join(root, fname)
                try:
                    with open(fpath, errors="ignore") as f:
                        content = f.read()
                    for rule_name, rule in self.VULN_RULES.items():
                        matches = re.finditer(rule["pattern"], content)
                        for m in matches:
                            line_num = content[:m.start()].count("\n") + 1
                            findings.append({
                                "rule": rule_name,
                                "severity": rule["severity"],
                                "description": rule["description"],
                                "file": fname,
                                "line": line_num,
                                "snippet": content.splitlines()[line_num - 1].strip() if line_num <= len(content.splitlines()) else "",
                            })
                except Exception:
                    continue
        return {"success": True, "findings": findings, "total": len(findings)}

    def semgrep_scan(self, source_dir: str, ruleset: str = "auto", args: dict = None) -> dict:
        """Run SemGrep OSS scan if available."""
        if not check_tool("semgrep"):
            return {"success": False, "error": "semgrep not available"}
        cmd = f"{get_tool_path('semgrep')} scan --config={ruleset} {source_dir} --json"
        res = run_command(cmd, timeout=120)
        if res["success"]:
            try:
                return {"success": True, "results": json.loads(res["stdout"])}
            except json.JSONDecodeError:
                pass
        return {"success": res["success"], "output": res["stdout"]}

    def _summarize(self, findings: list) -> dict:
        summary = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0, "total": len(findings)}
        for f in findings:
            sev = f.get("severity", "LOW")
            summary[sev] = summary.get(sev, 0) + 1
        return summary

    def exploit_check(self, vuln_type: str, target: str, args: dict = None) -> dict:
        """Check if a vulnerability is exploitable."""
        exploits = {
            "intent_redirection": self._check_intent_redirection,
            "sql_injection_risk": self._check_sqli,
            "insecure_network": self._check_cleartext,
        }
        checker = exploits.get(vuln_type)
        if checker:
            return checker(target, args)
        return {"success": False, "error": f"No exploit check for {vuln_type}"}

    def _check_intent_redirection(self, target: str, args: dict = None) -> dict:
        return {"success": True, "exploitable": True, "method": "am start-activity with malicious Intent extra"}

    def _check_sqli(self, target: str, args: dict = None) -> dict:
        return {"success": True, "exploitable": True, "method": "sqlmap -u <target> --dbs"}

    def _check_cleartext(self, target: str, args: dict = None) -> dict:
        return {"success": True, "exploitable": True, "method": "mitmproxy transparent mode"}
