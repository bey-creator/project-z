#!/bin/bash
# CyberLab Pro v3.0 — Build Verification Script
# Checks that all required binaries and sources are present

set -e

ASSETS_DIR="$(cd "$(dirname "$0")/../android/app/src/main/assets" && pwd)"
BINARIES_DIR="$ASSETS_DIR/binaries"
PYTHON_DIR="$ASSETS_DIR/python"
WORDLISTS_DIR="$ASSETS_DIR/wordlists"

echo "============================================"
echo "  Build Verification"
echo "============================================"

ERRORS=0
WARNINGS=0

# Check native binaries
echo "[*] Checking native binaries..."
NATIVE_TOOLS=(
    "nmap" "aircrack-ng" "airodump-ng" "aireplay-ng" "airmon-ng"
    "john" "hashcat" "hydra" "crunch"
    "masscan" "tcpdump" "netdiscover" "responder"
    "gobuster" "ffuf"
    "arpspoof" "mitmproxy"
    "cameradar" "searchsploit"
    "scrcpy" "apktool" "jadx" "frida" "frida-server"
    "exiftool" "foremost" "steghide"
    "lynis" "rkhunter"
    "macchanger" "iw" "iwconfig"
)

for tool in "${NATIVE_TOOLS[@]}"; do
    if [ -f "$BINARIES_DIR/$tool" ] || [ -f "$BINARIES_DIR/$tool.jar" ]; then
        echo "  [✓] $tool"
    else
        echo "  [✗] $tool MISSING"
        ((ERRORS++))
    fi
done

# Check Python tools
echo ""
echo "[*] Checking Python tool sources..."
PYTHON_TOOLS=(
    "sqlmap/sqlmap.py" "nikto/nikto.pl" "wfuzz/__init__.py"
    "routersploit/interpreter.py" "maigret/maigret.py"
    "holehe/core.py" "photon/__init__.py"
    "instaloader/__main__.py" "snscrape/__init__.py"
    "h8mail/main.py" "osintgram/main.py"
    "volatility/cli.py" "hash-identifier/h8_md5.py"
    "cewl/cewl.py" "binwalk/__init__.py"
    "wifite/wifite.py" "airgeddon/airgeddon.py"
    "impacket" "phoneinfoga/main.py"
)

for tool in "${PYTHON_TOOLS[@]}"; do
    if [ -e "$PYTHON_DIR/tools_py/$tool" ]; then
        echo "  [✓] $tool"
    else
        echo "  [!] $tool not bundled (will use pip install)"
        ((WARNINGS++))
    fi
done

# Check core Python modules
echo ""
echo "[*] Checking core Python modules..."
CORE_MODULES=(
    "core/utils.py" "core/wireless.py" "core/network.py"
    "core/cctv.py" "core/mitm.py" "core/cracker.py"
    "core/portal_forge.py" "core_bridge.py" "py_runner.py"
)

for mod in "${CORE_MODULES[@]}"; do
    if [ -f "$PYTHON_DIR/$mod" ]; then
        echo "  [✓] $mod"
    else
        echo "  [✗] $mod MISSING"
        ((ERRORS++))
    fi
done

# Check wordlists
echo ""
echo "[*] Checking wordlists..."
WORDLISTS=("rockyou.txt" "common_100k.txt" "cctv_defaults.txt" "best64.rule" "dive.rule" "passwords.lst" "fasttrack.txt")

for wl in "${WORDLISTS[@]}"; do
    if [ -f "$WORDLISTS_DIR/$wl" ]; then
        echo "  [✓] $wl"
    else
        echo "  [!] $wl missing"
        ((WARNINGS++))
    fi
done

# Check manifest
echo ""
echo "[*] Checking tools_manifest.json..."
if [ -f "$ASSETS_DIR/tools_manifest.json" ]; then
    echo "  [✓] tools_manifest.json present"
    TOOL_COUNT=$(python3 -c "import json; d=json.load(open('$ASSETS_DIR/tools_manifest.json')); print(len(d.get('tools', {})))" 2>/dev/null || echo "?")
    echo "  [*] $TOOL_COUNT tools in manifest"
else
    echo "  [✗] tools_manifest.json MISSING"
    ((ERRORS++))
fi

# Summary
echo ""
echo "============================================"
echo "  Verification Summary"
echo "============================================"
echo "  Errors:   $ERRORS"
echo "  Warnings: $WARNINGS"
echo ""

if [ $ERRORS -gt 0 ]; then
    echo "  [✗] BUILD NOT READY — fix errors above"
    exit 1
else
    echo "  [✓] BUILD READY — APK can be compiled"
    exit 0
fi
