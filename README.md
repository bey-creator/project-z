# CyberLab Pro v3.0

Android security assessment suite. Standalone APK with 58 pre-built security tools.

## Build

This repo uses GitHub Actions to build ARM64 binaries in the cloud.

1. Push to main → binaries build automatically
2. Download artifact from Actions → extract to `android/app/src/main/assets/`
3. Build APK via `build-apk.yml` workflow or locally

## Architecture

- React Native + TypeScript UI
- Java BinaryExecutor for native binaries (nmap, john, hashcat, etc.)
- Chaquopy for Python tools (sqlmap, nikto, routersploit, etc.)
- 10 categories, 58 tools

## License

MIT
