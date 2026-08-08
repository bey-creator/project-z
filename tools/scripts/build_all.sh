#!/bin/bash
# CyberLab Pro v3.0 — ARM64 Binary Acquisition Pipeline
# Compiles and downloads all native security tools for Android ARM64
# Run this on a Linux build machine with Docker installed

set -e

BUILD_DIR="$(cd "$(dirname "$0")/../build" && pwd)"
OUTPUT_DIR="$(cd "$(dirname "$0")/../android/app/src/main/assets/binaries" && pwd)"
WORDLIST_DIR="$(cd "$(dirname "$0")/../android/app/src/main/assets/wordlists" && pwd)"

mkdir -p "$BUILD_DIR" "$OUTPUT_DIR" "$WORDLIST_DIR"

echo "============================================"
echo "  CyberLab Pro — ARM64 Binary Builder"
echo "============================================"

# ============================================
# Tier 1: Download pre-built ARM64 binaries
# ============================================
echo "[*] Tier 1: Downloading pre-built ARM64 binaries..."

download_prebuilt() {
    local name="$1" url="$2"
    echo "  [>] Downloading $name..."
    if curl -fsSL "$url" -o "$OUTPUT_DIR/$name" 2>/dev/null; then
        chmod +x "$OUTPUT_DIR/$name"
        echo "  [✓] $name downloaded"
    else
        echo "  [✗] Failed to download $name"
    fi
}

# nmap — use official ARM64 build
download_prebuilt "nmap" "https://nmap.org/dist/nmap-7.94-linux-arm64.tar.bz2"

# aircrack-ng — compile from source
echo "  [>] Building aircrack-ng..."
cd "$BUILD_DIR"
if [ ! -d "aircrack-ng" ]; then
    git clone https://github.com/aircrack-ng/aircrack-ng.git
fi
cd aircrack-ng
git pull
autoreconf -i
./configure --host=aarch64-linux-gnu --prefix="$OUTPUT_DIR" CFLAGS="-static"
make -j$(nproc)
make install
echo "  [✓] aircrack-ng built"

# john (Openwall) — compile for ARM64
echo "  [>] Building john..."
cd "$BUILD_DIR"
if [ ! -d "john" ]; then
    git clone https://github.com/openwall/john.git
fi
cd john/src
./configure --host=aarch64-linux-gnu --disable-openmp
make -j$(nproc)
cp ../run/john "$OUTPUT_DIR/john"
chmod +x "$OUTPUT_DIR/john"
echo "  [✓] john built"

# hashcat — download ARM64 binary
download_prebuilt "hashcat" "https://hashcat.net/files/hashcat-6.2.6.7z"

# hydra — compile for ARM64
echo "  [>] Building hydra..."
cd "$BUILD_DIR"
if [ ! -d "thc-hydra" ]; then
    git clone https://github.com/vanhauser-thc/thc-hydra.git
fi
cd thc-hydra
git pull
./configure --host=aarch64-linux-gnu --prefix="$OUTPUT_DIR"
make -j$(nproc)
make install
echo "  [✓] hydra built"

# masscan — compile for ARM64
echo "  [>] Building masscan..."
cd "$BUILD_DIR"
if [ ! -d "masscan" ]; then
    git clone https://github.com/robertdavidgraham/masscan.git
fi
cd masscan
git pull
make -j$(nproc) CC=aarch64-linux-gnu-gcc
cp bin/masscan "$OUTPUT_DIR/masscan"
chmod +x "$OUTPUT_DIR/masscan"
echo "  [✓] masscan built"

# tcpdump + libpcap — compile for ARM64
echo "  [>] Building tcpdump..."
cd "$BUILD_DIR"
if [ ! -d "libpcap" ]; then
    git clone https://github.com/the-tcpdump-group/libpcap.git
fi
cd libpcap
git pull
./configure --host=aarch64-linux-gnu --prefix="$OUTPUT_DIR" --disable-usb --disable-netmap
make -j$(nproc)
make install
cd "$BUILD_DIR"
if [ ! -d "tcpdump" ]; then
    git clone https://github.com/the-tcpdump-group/tcpdump.git
fi
cd tcpdump
git pull
./configure --host=aarch64-linux-gnu --prefix="$OUTPUT_DIR"
make -j$(nproc)
make install
echo "  [✓] tcpdump built"

# gobuster — cross-compile Go
echo "  [>] Building gobuster..."
cd "$BUILD_DIR"
if [ ! -d "gobuster" ]; then
    git clone https://github.com/OJ/gobuster.git
fi
cd gobuster
git pull
GOOS=linux GOARCH=arm64 go build -o "$OUTPUT_DIR/gobuster" .
chmod +x "$OUTPUT_DIR/gobuster"
echo "  [✓] gobuster built"

# ffuf — cross-compile Go
echo "  [>] Building ffuf..."
cd "$BUILD_DIR"
if [ ! -d "ffuf" ]; then
    git clone https://github.com/ffuf/ffuf.git
fi
cd ffuf
git pull
GOOS=linux GOARCH=arm64 go build -o "$OUTPUT_DIR/ffuf" .
chmod +x "$OUTPUT_DIR/ffuf"
echo "  [✓] ffuf built"

# cameradar — cross-compile Go
echo "  [>] Building cameradar..."
cd "$BUILD_DIR"
if [ ! -d "cameradar" ]; then
    git clone https://github.com/Ullaakut/cameradar.git
fi
cd cameradar
git pull
GOOS=linux GOARCH=arm64 go build -o "$OUTPUT_DIR/cameradar" .
chmod +x "$OUTPUT_DIR/cameradar"
echo "  [✓] cameradar built"

# binwalk — pure Python, copy source
echo "  [>] Bundling binwalk (Python)..."
cd "$BUILD_DIR"
if [ ! -d "binwalk" ]; then
    git clone https://github.com/ReFirmLabs/binwalk.git
fi
cd binwalk
git pull
mkdir -p "$OUTPUT_DIR/binwalk_mod"
cp -r src/* "$OUTPUT_DIR/binwalk_mod/"
echo "  [✓] binwalk bundled"

# foremost — compile for ARM64
echo "  [>] Building foremost..."
cd "$BUILD_DIR"
if [ ! -d "foremost" ]; then
    git clone https://github.com/korczis/foremost.git
fi
cd foremost
git pull
make DESTDIR="$OUTPUT_DIR" CFLAGS="-static"
cp foremost "$OUTPUT_DIR/foremost"
chmod +x "$OUTPUT_DIR/foremost"
echo "  [✓] foremost built"

# steghide — compile for ARM64
echo "  [>] Building steghide..."
cd "$BUILD_DIR"
if [ ! -d "steghide" ]; then
    git clone https://github.com/steghide/steghide.git
fi
cd steghide
git pull
mkdir -p build && cd build
cmake .. -DCMAKE_TOOLCHAIN_FILE="$BUILD_DIR/aarch64-toolchain.cmake" -DCMAKE_INSTALL_PREFIX="$OUTPUT_DIR"
make -j$(nproc)
make install
echo "  [✓] steghide built"

# exiftool — pure Perl, copy
echo "  [>] Bundling exiftool (Perl)..."
cd "$BUILD_DIR"
if [ ! -d "exiftool" ]; then
    git clone https://github.com/exiftool/exiftool.git
fi
cd exiftool
git pull
mkdir -p "$OUTPUT_DIR/exiftool_mod"
cp -r lib/* "$OUTPUT_DIR/exiftool_mod/"
cp exiftool "$OUTPUT_DIR/"
chmod +x "$OUTPUT_DIR/exiftool"
echo "  [✓] exiftool bundled"

# apktool — Java, download jar
echo "  [>] Downloading apktool..."
curl -fsSL "https://bitbucket.org/iBotPeaches/apktool/downloads/apktool_2.9.3.jar" -o "$OUTPUT_DIR/apktool.jar"
echo "  [✓] apktool downloaded"

# jadx — download ARM64
echo "  [>] Downloading jadx..."
JADX_VERSION=$(curl -s https://api.github.com/repos/skylot/jadx/releases/latest | grep tag_name | cut -d '"' -f 4)
curl -fsSL "https://github.com/skylot/jadx/releases/download/$JADX_VERSION/jadx-$JADX_VERSION.zip" -o "$BUILD_DIR/jadx.zip"
unzip -o "$BUILD_DIR/jadx.zip" -d "$OUTPUT_DIR/jadx/"
echo "  [✓] jadx downloaded"

# frida — download ARM64 server
echo "  [>] Downloading frida-server..."
FRIDA_VERSION=$(curl -s https://api.github.com/repos/frida/frida/releases/latest | grep tag_name | cut -d '"' -f 4)
curl -fsSL "https://github.com/frida/frida/releases/download/$FRIDA_VERSION/frida-server-$FRIDA_VERSION-android-arm64.xz" -o "$OUTPUT_DIR/frida-server.xz"
xz -d "$OUTPUT_DIR/frida-server.xz"
mv "$OUTPUT_DIR/frida-server-$FRIDA_VERSION-android-arm64" "$OUTPUT_DIR/frida-server"
chmod +x "$OUTPUT_DIR/frida-server"
echo "  [✓] frida-server downloaded"

# searchsploit — copy (script + database)
echo "  [>] Bundling searchsploit..."
cd "$BUILD_DIR"
if [ ! -d "exploitdb" ]; then
    git clone https://github.com/offensive-security/exploitdb.git
fi
cd exploitdb
git pull
cp searchsploit "$OUTPUT_DIR/searchsploit"
chmod +x "$OUTPUT_DIR/searchsploit"
mkdir -p "$OUTPUT_DIR/searchsploit_dir"
cp -r files_csv.csv "$OUTPUT_DIR/searchsploit_dir/"
echo "  [✓] searchsploit bundled"

# lynis — copy (shell script)
echo "  [>] Bundling lynis..."
cd "$BUILD_DIR"
if [ ! -d "lynis" ]; then
    git clone https://github.com/CISOfy/lynis.git
fi
cd lynis
git pull
cp lynis "$OUTPUT_DIR/lynis"
chmod +x "$OUTPUT_DIR/lynis"
echo "  [✓] lynis bundled"

# rkhunter — copy (shell script)
echo "  [>] Bundling rkhunter..."
cd "$BUILD_DIR"
if [ ! -d "rkhunter" ]; then
    git clone https://github.com/installation/rkhunter.git
fi
cd rkhunter
git pull
cp rkhunter "$OUTPUT_DIR/rkhunter"
chmod +x "$OUTPUT_DIR/rkhunter"
echo "  [✓] rkhunter bundled"

# dsniff (arpspoof) — compile for ARM64
echo "  [>] Building dsniff (arpspoof)..."
cd "$BUILD_DIR"
if [ ! -d "dsniff" ]; then
    git clone https://github.com/dunbar/cyberdsniff.git dsniff
fi
cd dsniff
git pull
./configure --host=aarch64-linux-gnu --prefix="$OUTPUT_DIR"
make -j$(nproc)
cp arpspoof/arpspoof "$OUTPUT_DIR/arpspoof"
chmod +x "$OUTPUT_DIR/arpspoof"
echo "  [✓] arpspoof built"

# ============================================
# Tier 2: Wordlists
# ============================================
echo ""
echo "[*] Downloading wordlists..."
download_wordlist() {
    local name="$1" url="$2"
    echo "  [>] Downloading $name..."
    curl -fsSL "$url" -o "$WORDLIST_DIR/$name"
    echo "  [✓] $name downloaded"
}

download_wordlist "rockyou.txt" "https://github.com/brannondorsey/naive-hashcat/releases/download/data/rockyou.txt"
download_wordlist "common_100k.txt" "https://raw.githubusercontent.com/danielmiessler/SecLists/master/Passwords/Common-Credentials/10-million-password-list-top-100000.txt"
download_wordlist "cctv_defaults.txt" "https://raw.githubusercontent.com/abandon-secure/Default-CCTV-Credentials/master/userpass.txt"
download_wordlist "best64.rule" "https://raw.githubusercontent.com/hashcat/hashcat/master/rules/best64.rule"
download_wordlist "dive.rule" "https://raw.githubusercontent.com/hashcat/hashcat/master/rules/dive.rule"
download_wordlist "passwords.lst" "https://raw.githubusercontent.com/danielmiessler/SecLists/master/Passwords/Leaked-Databases/NordPass.txt"
download_wordlist "fasttrack.txt" "https://raw.githubusercontent.com/danielmiessler/SecLists/master/Passwords/darkweb2017-top100.txt"

# ============================================
# Final verification
# ============================================
echo ""
echo "============================================"
echo "  Build Complete"
echo "============================================"
echo "[*] Binaries in $OUTPUT_DIR:"
ls -la "$OUTPUT_DIR/" | grep -v "^d" | awk '{print "  " $9, $5}'
echo ""
echo "[*] Wordlists in $WORDLIST_DIR:"
ls -la "$WORDLIST_DIR/" | awk '{print "  " $9, $5}'
echo ""
echo "[✓] All tools ready for APK bundling"
