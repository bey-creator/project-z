#!/bin/bash
# CyberLab Pro v3.0 — Python Tool Source Bundler
# Downloads and bundles all Python-native tool source code

set -e

BUILD_DIR="$(cd "$(dirname "$0")/../build" && pwd)"
OUTPUT_DIR="$(cd "$(dirname "$0")/../android/app/src/main/assets/python/tools_py" && pwd)"

mkdir -p "$BUILD_DIR" "$OUTPUT_DIR"

echo "============================================"
echo "  Python Tool Source Bundler"
echo "==========================================="

clone_tool() {
    local name="$1" url="$2" subdir="$3"
    echo "  [>] Cloning $name..."
    if [ -d "$BUILD_DIR/$name" ]; then
        cd "$BUILD_DIR/$name" && git pull
    else
        git clone "$url" "$BUILD_DIR/$name"
    fi
    mkdir -p "$OUTPUT_DIR/$name"
    if [ -n "$subdir" ]; then
        cp -r "$BUILD_DIR/$name/$subdir"/* "$OUTPUT_DIR/$name/"
    else
        cp -r "$BUILD_DIR/$name"/* "$OUTPUT_DIR/$name/"
    fi
    echo "  [✓] $name bundled"
}

# Web tools
clone_tool "sqlmap" "https://github.com/sqlmapproject/sqlmap.git" ""
clone_tool "nikto" "https://github.com/sullo/nikto.git" "program"
clone_tool "wfuzz" "https://github.com/xmendez/wfuzz.git" "src"

# Device tools
clone_tool "routersploit" "https://github.com/threat9/routersploit.git" ""

# OSINT tools
clone_tool "maigret" "https://github.com/soxoj/maigret.git" ""
clone_tool "holehe" "https://github.com/megadose/holehe.git" ""
clone_tool "photon" "https://github.com/s0md3v/photon.git" "photon"
clone_tool "instaloader" "https://github.com/instaloader/instaloader.git" ""
clone_tool "snscrape" "https://github.com/JustAnotherArchivist/snscrape.git" ""
clone_tool "h8mail" "https://github.com/khast3x/h8mail.git" ""
clone_tool "osintgram" "https://github.com/Datalux/Osintgram.git" ""

# Forensic tools
clone_tool "volatility" "https://github.com/volatilityfoundation/volatility.git" ""

# Password tools
clone_tool "hash-identifier" "https://github.com/blackploit/hash-identifier.git" ""
clone_tool "cewl" "https://github.com/digininja/cewl.git" ""

# Wireless tools
clone_tool "wifite" "https://github.com/derv82/wifite.git" ""
clone_tool "airgeddon" "https://github.com/v1s1t0r1sh3r3/airgeddon.git" ""

# Network tools
clone_tool "impacket" "https://github.com/SecureAuthCorp/impacket.git" ""

# OSINT phone
clone_tool "phoneinfoga" "https://github.com/sundowndev/phoneinfoga.git" ""

echo ""
echo "============================================"
echo "  Python Tools Bundled"
echo "============================================"
echo "[*] Tools in $OUTPUT_DIR:"
ls -1 "$OUTPUT_DIR/"
echo ""
echo "[✓] All Python tool sources ready for Chaquopy"
