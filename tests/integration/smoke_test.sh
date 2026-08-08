#!/bin/bash
# CyberLab Pro v3.0 — Smoke Test Suite
# Tests each tool's basic functionality on the device

set -e

ASSETS_DIR="$(cd "$(dirname "$0")/../android/app/src/main/assets" && pwd)"
BINARIES_DIR="$ASSETS_DIR/binaries"

echo "============================================"
echo "  Smoke Test Suite"
echo "============================================"

PASS=0
FAIL=0

test_binary() {
    local name="$1" cmd="$2"
    echo -n "  Testing $name... "
    if eval "$cmd" > /dev/null 2>&1; then
        echo "PASS"
        ((PASS++))
    else
        echo "FAIL"
        ((FAIL++))
    fi
}

# Native binary tests
echo "[*] Native binaries..."
test_binary "nmap" "$BINARIES_DIR/nmap --version"
test_binary "aircrack-ng" "$BINARIES_DIR/aircrack-ng --help"
test_binary "john" "$BINARIES_DIR/john --version"
test_binary "hashcat" "$BINARIES_DIR/hashcat --version"
test_binary "hydra" "$BINARIES_DIR/hydra -h"
test_binary "masscan" "$BINARIES_DIR/masscan --echo"
test_binary "tcpdump" "$BINARIES_DIR/tcpdump --version"
test_binary "gobuster" "$BINARIES_DIR/gobuster version"
test_binary "ffuf" "$BINARIES_DIR/ffuf -V"
test_binary "arpspoof" "$BINARIES_DIR/arpspoof --help"
test_binary "cameradar" "$BINARIES_DIR/cameradar --help"
test_binary "foremost" "$BINARIES_DIR/foremost -h"
test_binary "steghide" "$BINARIES_DIR/steghide --version"
test_binary "exiftool" "$BINARIES_DIR/exiftool -ver"
test_binary "searchsploit" "$BINARIES_DIR/searchsploit --help"
test_binary "lynis" "$BINARIES_DIR/lynis show version"
test_binary "rkhunter" "$BINARIES_DIR/rkhunter --version"
test_binary "macchanger" "$BINARIES_DIR/macchanger --help"
test_binary "iw" "$BINARIES_DIR/iw --version"

# Python tool tests
echo ""
echo "[*] Python tools..."
test_binary "sqlmap" "python3 $ASSETS_DIR/python/tools_py/sqlmap/sqlmap.py --version"
test_binary "nikto" "perl $ASSETS_DIR/python/tools_py/nikto/nikto.pl -Version"
test_binary "routersploit" "python3 $ASSETS_DIR/python/tools_py/routersploit/interpreter.py --help"
test_binary "maigret" "python3 $ASSETS_DIR/python/tools_py/maigret/maigret.py --version"
test_binary "holehe" "python3 $ASSETS_DIR/python/tools_py/holehe/core.py --help"
test_binary "binwalk" "python3 $ASSETS_DIR/python/tools_py/binwalk/__init__.py"
test_binary "cewl" "ruby $ASSETS_DIR/python/tools_py/cewl/cewl.rb --help"
test_binary "wifite" "python3 $ASSETS_DIR/python/tools_py/wifite/wifite.py --help"

# Summary
echo ""
echo "============================================"
echo "  Smoke Test Summary"
echo "============================================"
echo "  Passed: $PASS"
echo "  Failed: $FAIL"
echo ""

if [ $FAIL -gt 0 ]; then
    echo "  [✗] Some tests failed"
    exit 1
else
    echo "  [✓] All tests passed"
    exit 0
fi
