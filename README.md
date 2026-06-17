# UID-Generator
![Python](https://img.shields.io/badge/Python-3.11%2B-brightgreen?logo=python&logoColor=white)
![Version](https://img.shields.io/badge/Version-1.1%20Beta-blueviolet)
![License](https://img.shields.io/github/license/Sketchware-TM/UID-Generator?logo=github)
![Platform](https://img.shields.io/badge/Platform-Linux%20%7C%20Windows%20(WSL)%20%7C%20Android-lightgrey?logo=linux&logoColor=white)

## 🛡️ Military Grade UID Generator & Licensing System

A powerful Python-based security tool to generate unique, hardware-bound UIDs for device authentication. It features a built-in time-based access control system to manage and restrict device-specific entry.

## ⚠️ Warning
As the creator of this script, I do not recommend using this as the sole authentication layer for production websites or applications. While v1.1 Beta upgrades password protection to AES (Fernet) wrapped in XOR encoding instead of plain XOR + Base64, it's still best suited for personal projects, license-gating scripts, and device-binding tools rather than critical production auth.

## 🆕 What's New in v1.1 Beta
* **Triple-Layer Encryption**: Passwords are now protected with AES (Fernet) derived via PBKDF2-HMAC-SHA256 (100k iterations), then wrapped again in XOR encoding.
* **Multi-Format UID Generation**: Generate `DEFAULT`, `SCRU160`, `NANO`, `UUID4`, or `ALL` formats at once.
* **CRC32 Checksum**: Default-format UIDs now embed a checksum for tamper/typo detection.
* **Collision Guard ("Battlefield Mode")**: Automatically detects and regenerates on ID collisions.
* **New Commands**: `--delete`, `--export`, and `--verify` for full UID lifecycle management.
* **Integrity Checksum**: Generated UID data is hashed (SHA-256) and stored alongside the license file.

### 🚀 Key Features
* **Hardware Binding**: UIDs are uniquely generated based on device fingerprinting (OS, Hostname, Architecture, and Android device props when available).
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