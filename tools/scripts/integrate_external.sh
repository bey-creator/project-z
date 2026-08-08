#!/bin/bash
# CyberLab Pro v3.0 — External Repo Integration
# Extracts and integrates tools from external GitHub repos

set -e

BUILD_DIR="$(cd "$(dirname "$0")/../build" && pwd)"
EXTERNAL_DIR="$(cd "$(dirname "$0")/../android/app/src/main/assets/external" && pwd)"

mkdir -p "$BUILD_DIR" "$EXTERNAL_DIR"

echo "============================================"
echo "  External Repo Tool Integration"
echo "============================================"

# === Jiutian (玖天) — Android pentest toolkit ===
echo "[*] Integrating jiutian toolkit..."
cd "$BUILD_DIR"
if [ ! -d "jiutian" ]; then
    git clone https://github.com/fairysy/jiutian.git
fi
cd jiutian && git pull
# jiutian is an Android APK — extract its tools
mkdir -p "$EXTERNAL_DIR/jiutian"
# Copy scanning modules (decompile APK for source)
cp -r app/src/main/java/com/pentest/* "$EXTERNAL_DIR/jiutian/" 2>/dev/null || true
echo "  [✓] jiutian integrated"

# === XHunter — Android RAT/pen tool ===
echo "[*] Integrating xhunter..."
cd "$BUILD_DIR"
if [ ! -d "xhunter" ]; then
    git clone https://github.com/anirudhmalik/xhunter.git
fi
cd xhunter && git pull
mkdir -p "$EXTERNAL_DIR/xhunter"
# xhunter has binder, nmap module, SSH tunnel — copy source
cp -r binder "$EXTERNAL_DIR/xhunter/" 2>/dev/null || true
cp -r app/src/main/java/* "$EXTERNAL_DIR/xhunter/" 2>/dev/null || true
echo "  [✓] xhunter integrated"

# === Sherlock — Android static analyzer ===
echo "[*] Integrating sherlock..."
cd "$BUILD_DIR"
if [ ! -d "sherlock" ]; then
    git clone https://github.com/matauangcina/sherlock.git
fi
cd sherlock && git pull
mkdir -p "$EXTERNAL_DIR/sherlock"
# sherlock is Python — copy source
cp -r modules "$EXTERNAL_DIR/sherlock/"
cp -r rules "$EXTERNAL_DIR/sherlock/"
cp -r commands "$EXTERNAL_DIR/sherlock/"
cp sherlock.py "$EXTERNAL_DIR/sherlock/"
cp globals.py "$EXTERNAL_DIR/sherlock/"
cp requirements.txt "$EXTERNAL_DIR/sherlock/"
echo "  [✓] sherlock integrated"

# === Evil-Droid — APK payload builder ===
echo "[*] Integrating evil-droid..."
cd "$BUILD_DIR"
if [ ! -d "evil-droid" ]; then
    git clone https://github.com/pythonplayer396/evil-droid.git
fi
cd evil-droid && git pull
mkdir -p "$EXTERNAL_DIR/evil-droid"
cp evil-droid "$EXTERNAL_DIR/evil-droid/"
cp -r tools "$EXTERNAL_DIR/evil-droid/"
cp -r icons "$EXTERNAL_DIR/evil-droid/"
chmod +x "$EXTERNAL_DIR/evil-droid/evil-droid"
echo "  [✓] evil-droid integrated"

# === RedTiger Tools ===
echo "[*] Integrating redtiger-tools..."
cd "$BUILD_DIR"
if [ ! -d "redtiger" ]; then
    git clone https://github.com/Hackerd-825/RedTiger-Tools.git redtiger
fi
cd redtiger && git pull
mkdir -p "$EXTERNAL_DIR/redtiger"
cp RedTiger.py "$EXTERNAL_DIR/redtiger/"
cp -r Program "$EXTERNAL_DIR/redtiger/"
echo "  [✓] redtiger integrated"

echo ""
echo "============================================"
echo "  External Tools Integrated"
echo "============================================"
echo "[*] External tools in $EXTERNAL_DIR:"
ls -1 "$EXTERNAL_DIR/"
echo ""
echo "[✓] All external repos ready"
