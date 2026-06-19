# UID-Generator
![Python](https://img.shields.io/badge/Python-3.11%2B-brightgreen?logo=python&logoColor=white)
![Version](https://img.shields.io/badge/Version-1.1.1%20Beta-blueviolet)
![License](https://img.shields.io/github/license/Sketchware-TM/UID-Generator?logo=github)
![Platform](https://img.shields.io/badge/Platform-Linux%20%7C%20Windows%20(WSL)%20%7C%20Android-lightgrey?logo=linux&logoColor=white)

## 🛡️ Military Grade UID Generator & Licensing System

A powerful Python-based security tool to generate unique, hardware-bound UIDs for device authentication. It features a built-in time-based access control system to manage and restrict device-specific entry.

## ⚠️ Warning
As the creator of this script, I do not recommend using this as the sole authentication layer for production websites or applications. v1.1.1 hardens integrity checks by replacing CRC32/plain SHA-256 with HMAC-SHA256 throughout, and binds each UID to its device fingerprint — but it's still best suited for personal projects, license-gating scripts, and device-binding tools rather than critical production auth.

## 🆕 What's New in v1.1.1 Beta
* **HMAC-SHA256 Everywhere**: CRC32 and plain SHA-256 checksums are fully retired. Default-format UIDs, the saved license file, and the renew flow now all use HMAC-SHA256, so tampering requires the secret key, not just guesswork.
* **Fingerprint Binding**: Every UID is cryptographically bound to its device via a dedicated `FINGERPRINT_BINDING` field — copying a valid UID + password to another device no longer passes verification.
* **Stronger Device Fingerprint**: Fingerprinting now combines machine ID, OS/architecture/CPU info, Android system properties (with MAC-address fallback), hostname, and a day-based time salt, hashed with SHA3-512.
* **Adaptive Progress Bar**: Terminal progress bar auto-sizes to the current terminal width so it doesn't wrap or clip on narrow screens (Termux-friendly).
* **Triple-Layer Encryption**: Passwords remain protected with AES (Fernet) derived via PBKDF2-HMAC-SHA256 (100k iterations), then wrapped again in XOR encoding.
* **Multi-Format UID Generation**: Generate `DEFAULT`, `SCRU160`, `NANO`, `UUID4`, or `ALL` formats at once.
* **Collision Guard ("Battlefield Mode")**: Automatically detects and regenerates on ID collisions.
* **Full Lifecycle Commands**: `--delete`, `--export`, and `--verify` for full UID lifecycle management.

### 🚀 Key Features
* **Hardware Binding**: UIDs are uniquely generated based on enhanced device fingerprinting (machine ID, OS, Hostname, Architecture, and Android device props when available) and cryptographically bound via HMAC.
* **Tamper-Proof Integrity**: All stored data is signed with HMAC-SHA256 — any modification to the UID file is detected on the next `--check` or `--verify`.
* **Dynamic Expiration**: Custom time duration from Seconds, Minutes, Hours, Days, Months, to Years.
* **Layered Encryption**: Protects UID passwords using AES (Fernet) + XOR encoding.
* **Multiple ID Formats**: Custom checksummed format, SCRU160, NanoID, and UUID4.
* **Progress Bar**: Beautiful terminal UI that adapts to your screen size (Termux/Linux/PC).

## ⚙️ Usage
1. Generate new UID (optionally pick a format)
```bash
python UIDGenerator.py --create [DEFAULT|SCRU160|NANO|UUID4|ALL]
```
2. Check Validity & Remaining Time
```bash
python UIDGenerator.py --check
```
3. Renew License
```bash
python UIDGenerator.py --renew <PASSWORD>
```
4. Show Recovered Password
```bash
python UIDGenerator.py --show-password
```
5. Verify a Generated UID
```bash
python UIDGenerator.py --verify <UID>
```
6. Export UID Data to JSON
```bash
python UIDGenerator.py --export
```
7. Delete the UID File
```bash
python UIDGenerator.py --delete
```

## Screenshot
![Screenshot](.assets/ss.png)

<p align="center">
  <img src="https://img.shields.io/badge/Made By-SkTeamProject-blue?style=for-the-badge&logo=github" alt="Collaborator">
  <img src="https://img.shields.io/badge/©-2026-blueviolet?style=for-the-badge" alt="Year">
</p>