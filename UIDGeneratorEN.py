#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import subprocess
import importlib
import json
import time
import secrets
import uuid
import base64
import hashlib
import zlib
import platform
import struct
import socket
import re
from datetime import datetime, timedelta

def install_package(package):
    subprocess.check_call([sys.executable, "-m", "pip", "install", package])

def ensure_dependencies():
    required = {
        "cryptography": "cryptography",
        "colorama": "colorama"
    }
    for module, package in required.items():
        try:
            importlib.import_module(module)
        except ImportError:
            print(f"[*] Installing missing dependency: {package} ...")
            install_package(package)
            print(f"[+] {package} installed successfully.")

ensure_dependencies()

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from colorama import Fore, Style, init

init(autoreset=True)

FILE_NAME = "UID.md"
XOR_KEY = "lSoXWboNRdUsgOtzGdBbJxaoBdvGmYDWvjvZxzxIFoCFsfEUryLXnjDomACMGNIC"
SALT = b'\x05-\x17\x89h\xed\xb8\x9bM6m\x97_\xe3\x1auI\x91\xff\x81\x0can\x08\xc8G&\xcc^4\xb0-\xdaO;\x08w\xf6\xf80\xac\xd1a!1\xae~g\xed-W"\xad\xfb$\x08\xe5y:\xd4\xad\xa6\xb6\x07'
VERSION = "1.1 Beta"

BOLD = Style.BRIGHT
RESET = Style.RESET_ALL

def LOG_INFO(msg):
    print(f"{Fore.CYAN}{BOLD}[INFO]{RESET} {BOLD}{msg}{RESET}")

def LOG_WARN(msg):
    print(f"{Fore.YELLOW}{BOLD}[WARNING]{RESET} {Fore.YELLOW}{BOLD}{msg}{RESET}")

def LOG_ERROR(msg):
    print(f"{Fore.RED}{BOLD}[ERROR]{RESET} {Fore.RED}{BOLD}{msg}{RESET}")

def LOG_SUCCESS(msg):
    print(f"{Fore.GREEN}{BOLD}[SUCCESS]{RESET} {Fore.GREEN}{BOLD}{msg}{RESET}")

def generate_key_from_password(password: str, salt: bytes = None) -> bytes:
    if salt is None:
        salt = SALT
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
    )
    return base64.urlsafe_b64encode(kdf.derive(password.encode()))

def aes_encrypt(text: str, password: str) -> str:
    key = generate_key_from_password(password)
    f = Fernet(key)
    return f.encrypt(text.encode()).decode()

def aes_decrypt(encrypted: str, password: str) -> str:
    key = generate_key_from_password(password)
    f = Fernet(key)
    return f.decrypt(encrypted.encode()).decode()

def xor_encrypt(text: str, key: str) -> str:
    return base64.b64encode(
        "".join(chr(ord(c) ^ ord(key[i % len(key)])) for i, c in enumerate(text)).encode()
    ).decode()

def xor_decrypt(encoded: str, key: str) -> str:
    data = base64.b64decode(encoded).decode()
    return "".join(chr(ord(c) ^ ord(key[i % len(key)])) for i, c in enumerate(data))

def triple_encrypt(text: str, password: str) -> str:
    aes_encrypted = aes_encrypt(text, password)
    xor_encrypted = xor_encrypt(aes_encrypted, XOR_KEY)
    return xor_encrypted

def triple_decrypt(encoded: str, password: str) -> str:
    xor_decrypted = xor_decrypt(encoded, XOR_KEY)
    aes_decrypted = aes_decrypt(xor_decrypted, password)
    return aes_decrypted

def get_android_prop(prop_name):
    try:
        result = subprocess.check_output(['getprop', prop_name], text=True).strip()
        return result if result else None
    except:
        return None

def device_fingerprint() -> str:
    components = []
    components.append(platform.system())
    components.append(platform.machine())
    components.append(platform.architecture()[0])
    components.append(str(struct.calcsize("P") * 8))
    components.append(str(os.cpu_count()))

    android_props = ['ro.serialno', 'ro.product.device', 'ro.product.model']
    found_android = False
    for prop in android_props:
        val = get_android_prop(prop)
        if val:
            components.append(val)
            found_android = True

    if not found_android:
        mac = uuid.getnode()
        if mac & 0xFFFFFFFFFFFF:
            mac_str = f"{mac:012X}"
            components.append(mac_str)
        else:
            components.append("UNKNOWN-MAC")

    raw = "|".join(components)
    return hashlib.sha512(raw.encode()).hexdigest()

class UIDGenerator:
    def __init__(self):
        self.battlefield_mode = True
        self.generated_ids = set()
    
    def _generate_scr160(self) -> str:
        try:
            from scru160 import scru160
            return scru160()
        except ImportError:
            timestamp = int(time.time() * 1000)
            random_part = secrets.token_hex(20)
            return f"{timestamp:x}{random_part}".upper()[:32]
    
    def _generate_nanoid(self, size: int = 21) -> str:
        try:
            from nanoid import generate
            return generate(size=size)
        except ImportError:
            alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
            return "".join(secrets.choice(alphabet) for _ in range(size))
    
    def _generate_custom_format(self, prefix: str = "UID") -> str:
        parts = [
            prefix,
            secrets.token_hex(2).upper(),
            secrets.token_hex(2).upper(),
            secrets.token_hex(2).upper(),
            secrets.token_hex(2).upper(),
            secrets.token_hex(3).upper()
        ]
        return "-".join(parts)
    
    def generate(self, format_type: str = "DEFAULT", prefix: str = "UID") -> dict:
        timestamp = datetime.now().isoformat()
        fingerprint = device_fingerprint()[:32]
        
        result = {
            "timestamp": timestamp,
            "fingerprint": fingerprint,
            "version": VERSION,
            "formats": {}
        }
        
        if format_type in ["DEFAULT", "ALL"]:
            uid = self._generate_custom_format(prefix)
            checksum = zlib.crc32(uid.encode()) & 0xFFFFFFFF
            uid = f"{uid}-{checksum:08X}"
            result["formats"]["default"] = uid
        
        if format_type in ["SCRU160", "ALL"]:
            result["formats"]["scru160"] = self._generate_scr160()
        
        if format_type in ["NANO", "ALL"]:
            result["formats"]["nano"] = self._generate_nanoid()
        
        if format_type in ["UUID4", "ALL"]:
            result["formats"]["uuid4"] = str(uuid.uuid4()).upper()
        
        if self.battlefield_mode:
            for fmt, uid in result["formats"].items():
                if uid in self.generated_ids:
                    LOG_WARN(f"Collision detected on {fmt}! Regenerating...")
                    return self.generate(format_type, prefix)
                self.generated_ids.add(uid)
        
        return result

def get_expire_text(expire_dict):
    parts = []
    name_map = {
        "years": "Years",
        "months": "Months",
        "days": "Days",
        "hours": "Hours",
        "minutes": "Minutes",
        "seconds": "Seconds"
    }
    for unit, value in expire_dict.items():
        if value > 0:
            parts.append(f"{value} {name_map.get(unit, unit)}")
    return ", ".join(parts) if parts else "0 Seconds"

def expire_delta_from_text(expire_text):
    try:
        parts = expire_text.split()
        num = int(parts[0])
        unit = parts[1].lower()
        if "year" in unit: return timedelta(days=num*365)
        if "month" in unit: return timedelta(days=num*30)
        if "day" in unit: return timedelta(days=num)
        if "hour" in unit: return timedelta(hours=num)
        if "minute" in unit: return timedelta(minutes=num)
        if "second" in unit: return timedelta(seconds=num)
    except:
        pass
    return timedelta(days=365)

def human_time(seconds):
    units = [("Years", 31536000), ("Months", 2592000), ("Days", 86400),
             ("Hours", 3600), ("Minutes", 60), ("Seconds", 1)]
    out = []
    for name, size in units:
        val, seconds = divmod(seconds, size)
        if val:
            out.append(f"{val} {name}")
    return " ".join(out) or "0 Seconds"

def show_help():
    BOX_WIDTH = 54
    inner_width = BOX_WIDTH - 2
    title = f"UID GENERATOR v{VERSION}"
    left_pad = (inner_width - len(title)) // 2
    right_pad = inner_width - len(title) - left_pad

    color = Fore.MAGENTA + BOLD

    top_border = "╔" + "═" * inner_width + "╗"
    bottom_border = "╚" + "═" * inner_width + "╝"
    title_line = "║" + " " * left_pad + title + " " * right_pad + "║"

    print(color + "-" * BOX_WIDTH + RESET)
    print(color + top_border + RESET)
    print(color + title_line + RESET)
    print(color + bottom_border + RESET)

    print(f"\n{Fore.GREEN}{BOLD}▶ AVAILABLE COMMANDS:{RESET}")
    print(f"  python UIDGenerator.py --create [FORMAT]    Create a new UID")
    print(f"  python UIDGenerator.py --check              Check UID status")
    print(f"  python UIDGenerator.py --renew <PWD>        Extend UID validity")
    print(f"  python UIDGenerator.py --show-password      Display password")
    print(f"  python UIDGenerator.py --delete             Delete UID file")
    print(f"  python UIDGenerator.py --export             Export to JSON")
    print(f"  python UIDGenerator.py --verify <UID>       Verify an existing UID")
    
    print(f"\n{Fore.CYAN}{BOLD}▶ ID FORMATS:{RESET}")
    print(f"  DEFAULT   : XX-XXXX-XXXX-XXXX-XXXX-XXXX-XXXXXXXX (with checksum)")
    print(f"  SCRU160   : 32-char base32hex (time-sortable)")
    print(f"  NANO      : URL-friendly crypto-secure ID")
    print(f"  UUID4     : Standard UUID4")
    print(f"  ALL       : Generate all formats at once")
    
    print(f"\n{Fore.YELLOW}{BOLD}▶ EXAMPLES:{RESET}")
    print(f"  python UIDGenerator.py --create DEFAULT")
    print(f"  python UIDGenerator.py --create ALL")
    
    print(color + "-" * BOX_WIDTH + RESET + "\n")

def main():
    args = sys.argv[1:]
    
    if not args or "--help" in args or "-h" in args:
        show_help()
        return
    
    generator = UIDGenerator()
    
    if args[0] == "--create":
        if os.path.exists(FILE_NAME):
            LOG_WARN("UID already exists. Use --renew to extend.")
            return
        
        format_type = args[1].upper() if len(args) > 1 else "DEFAULT"
        valid_formats = ["DEFAULT", "SCRU160", "NANO", "UUID4", "ALL"]
        
        if format_type not in valid_formats:
            LOG_ERROR(f"Invalid format! Use: {', '.join(valid_formats)}")
            return
        
        print(f"\n{Fore.CYAN}{BOLD}SELECT EXPIRATION UNIT (SECONDS - YEARS):{RESET}")
        print(f" {Fore.WHITE}1. Seconds   2. Minutes   3. Hours")
        print(f" {Fore.WHITE}4. Days      5. Months   6. Years")
        
        expire_dict = {"years":0, "months":0, "days":0, "hours":0, "minutes":0, "seconds":0}
        
        try:
            choice = input(f"\n{Fore.WHITE}Enter choice (1-6): {Fore.YELLOW}").strip()
            unit_map = {
                "1": "seconds", "2": "minutes", "3": "hours",
                "4": "days", "5": "months", "6": "years"
            }
            display_map = {
                "1": "Seconds", "2": "Minutes", "3": "Hours",
                "4": "Days", "5": "Months", "6": "Years"
            }
            if choice in unit_map:
                unit_key = unit_map[choice]
                unit_display = display_map[choice]
                amount_input = input(f"{Fore.WHITE}Enter amount of {Fore.CYAN}{unit_display}{Fore.WHITE} (Default 1): {Fore.YELLOW}").strip()
                amount = int(amount_input) if amount_input != "" else 1
                if amount <= 0:
                    LOG_ERROR("Amount must be positive!")
                    return
                expire_dict[unit_key] = amount
            else:
                LOG_ERROR("Invalid choice!")
                return
        except ValueError:
            LOG_ERROR("Input must be a number!")
            return
        
        expire_text = get_expire_text(expire_dict)
        LOG_INFO(f"Expiry set to: {expire_text}")
        
        LOG_INFO(f"Generating {format_type} UID...")
        
        uid_data = generator.generate(format_type, prefix="UID")
        raw_password = secrets.token_urlsafe(16)
        encrypted_password = triple_encrypt(raw_password, XOR_KEY)
        
        with open(FILE_NAME, "w") as f:
            f.write(f"""# UID Information
# Generated: {uid_data['timestamp']}

UID_DATA : {json.dumps(uid_data)}
PASSWORD : {encrypted_password}
FINGERPRINT : {uid_data['fingerprint']}
CREATED_AT : {uid_data['timestamp']}
EXPIRY : {expire_text}

# INTEGRITY CHECKSUM
CHECKSUM : {hashlib.sha256(json.dumps(uid_data).encode()).hexdigest()[:16]}
""")
        
        LOG_SUCCESS("UID created successfully!")
        print(f"\n{Fore.WHITE}{'═'*60}")
        LOG_INFO(f"UID (default) : {Fore.YELLOW}{BOLD}{uid_data['formats'].get('default', 'N/A')}")
        LOG_INFO(f"SCRU160      : {Fore.YELLOW}{BOLD}{uid_data['formats'].get('scru160', 'N/A')}")
        LOG_INFO(f"NANO ID      : {Fore.YELLOW}{BOLD}{uid_data['formats'].get('nano', 'N/A')}")
        LOG_INFO(f"PASSWORD     : {Fore.RED}{BOLD}{raw_password}")
        LOG_INFO(f"FINGERPRINT  : {Fore.CYAN}{uid_data['fingerprint'][:16]}...")
        LOG_INFO(f"EXPIRY       : {Fore.YELLOW}{expire_text}")
        print(f"{Fore.WHITE}{'═'*60}")
        return
    
    if args[0] == "--check":
        if not os.path.exists(FILE_NAME):
            LOG_ERROR("UID not found. Create one with --create.")
            return
        
        with open(FILE_NAME, "r") as f:
            content = f.read()
        
        uid_data_str = re.search(r"UID_DATA\s*:\s*({.*})", content, re.DOTALL)
        fp_str = re.search(r"FINGERPRINT\s*:\s*(\S+)", content)
        created_str = re.search(r"CREATED_AT\s*:\s*(\S+)", content)
        expiry_str = re.search(r"EXPIRY\s*:\s*(.+)", content)
        
        if not uid_data_str or not fp_str or not created_str or not expiry_str:
            LOG_ERROR("Corrupted UID file.")
            return
        
        try:
            uid_json = json.loads(uid_data_str.group(1))
        except json.JSONDecodeError:
            for line in content.splitlines():
                if line.strip().startswith("UID_DATA"):
                    raw_json = line.split(":", 1)[1].strip()
                    uid_json = json.loads(raw_json)
                    break
            else:
                LOG_ERROR("Cannot parse UID_DATA.")
                return
        
        stored_fingerprint = fp_str.group(1).strip()
        created_at = datetime.fromisoformat(created_str.group(1).strip())
        expire_text = expiry_str.group(1).strip()
        
        current_fp = device_fingerprint()[:32]
        if stored_fingerprint != current_fp:
            LOG_ERROR("Access denied! Device fingerprint mismatch.")
            LOG_INFO(f"Stored: {stored_fingerprint}")
            LOG_INFO(f"Current: {current_fp}")
            return
        
        duration = expire_delta_from_text(expire_text)
        expire_date = created_at + duration
        remain = int((expire_date - datetime.now()).total_seconds())
        
        if remain <= 0:
            LOG_ERROR(f"UID expired on {expire_date.strftime('%Y-%m-%d %H:%M:%S')}")
        else:
            LOG_SUCCESS("UID is valid.")
            LOG_INFO(f"Time remaining: {Fore.GREEN}{human_time(remain)}")
            LOG_INFO(f"Expires: {expire_date.strftime('%Y-%m-%d %H:%M:%S')}")
        return
    
    if args[0] == "--show-password":
        if not os.path.exists(FILE_NAME):
            LOG_ERROR("File not found.")
            return
        
        with open(FILE_NAME, "r") as f:
            content = f.read()
        
        pwd_match = re.search(r"PASSWORD\s*:\s*(\S+)", content)
        if not pwd_match:
            LOG_ERROR("Password not found in file.")
            return
        encrypted = pwd_match.group(1).strip()
        try:
            decrypted = triple_decrypt(encrypted, XOR_KEY)
            LOG_INFO(f"Password: {Fore.RED}{BOLD}{decrypted}")
        except Exception as e:
            LOG_ERROR("Failed to decrypt password.")
            LOG_INFO("This may happen if you used an older version with random salt.")
            LOG_INFO("Please delete UID.md and create a new one with this version.")
        return
    
    if args[0] == "--renew" and len(args) > 1:
        provided_pwd = args[1]
        
        if not os.path.exists(FILE_NAME):
            LOG_ERROR("File not found.")
            return
        
        with open(FILE_NAME, "r") as f:
            content = f.read()
        
        pwd_match = re.search(r"PASSWORD\s*:\s*(\S+)", content)
        if not pwd_match:
            LOG_ERROR("Password not found.")
            return
        encrypted = pwd_match.group(1).strip()
        try:
            stored_pwd = triple_decrypt(encrypted, XOR_KEY)
            if provided_pwd != stored_pwd:
                LOG_ERROR("Incorrect password!")
                return
        except:
            LOG_ERROR("Failed to verify password.")
            return
        
        expiry_match = re.search(r"EXPIRY\s*:\s*(.+)", content)
        if not expiry_match:
            LOG_ERROR("Expiry not found.")
            return
        expire_text = expiry_match.group(1).strip()
        
        lines = content.splitlines()
        new_lines = []
        for line in lines:
            if line.strip().startswith("CREATED_AT"):
                new_lines.append(f"CREATED_AT : {datetime.now().isoformat()}")
            elif line.strip().startswith("EXPIRY"):
                new_lines.append(f"EXPIRY : {expire_text}")
            else:
                new_lines.append(line)
        
        with open(FILE_NAME, "w") as f:
            f.write("\n".join(new_lines))
        
        LOG_SUCCESS("UID renewed successfully!")
        LOG_INFO(f"New CREATED_AT: {datetime.now().isoformat()}")
        LOG_INFO(f"Expiry remains: {expire_text}")
        return
    
    if args[0] == "--delete":
        if os.path.exists(FILE_NAME):
            os.remove(FILE_NAME)
            LOG_SUCCESS("UID deleted.")
        else:
            LOG_WARN("No UID to delete.")
        return
    
    if args[0] == "--export":
        if not os.path.exists(FILE_NAME):
            LOG_ERROR("File not found.")
            return
        
        with open(FILE_NAME, "r") as f:
            content = f.read()
        
        export_data = {}
        for line in content.splitlines():
            if ":" in line and not line.startswith("#"):
                key, value = line.split(":", 1)
                export_data[key.strip()] = value.strip()
        
        with open("uid_export.json", "w") as f:
            json.dump(export_data, f, indent=2)
        
        LOG_SUCCESS("Exported to uid_export.json")
        return
    
    if args[0] == "--verify" and len(args) > 1:
        uid_to_verify = args[1].strip()
        
        if '-' not in uid_to_verify:
            LOG_ERROR("Invalid UID format. Must contain dashes.")
            return
        parts = uid_to_verify.split('-')
        if len(parts) < 2:
            LOG_ERROR("Invalid UID format. Expected at least two parts.")
            return
        
        if not os.path.exists(FILE_NAME):
            LOG_ERROR("UID file not found. Cannot verify.")
            return
        
        with open(FILE_NAME, "r") as f:
            content = f.read()
        
        uid_data_str = re.search(r"UID_DATA\s*:\s*({.*})", content, re.DOTALL)
        fp_match = re.search(r"FINGERPRINT\s*:\s*(\S+)", content)
        created_match = re.search(r"CREATED_AT\s*:\s*(\S+)", content)
        expiry_match = re.search(r"EXPIRY\s*:\s*(.+)", content)
        
        if not uid_data_str or not fp_match or not created_match or not expiry_match:
            LOG_ERROR("Corrupted UID file.")
            return
        
        try:
            uid_json = json.loads(uid_data_str.group(1))
        except json.JSONDecodeError:
            for line in content.splitlines():
                if line.strip().startswith("UID_DATA"):
                    raw_json = line.split(":", 1)[1].strip()
                    uid_json = json.loads(raw_json)
                    break
            else:
                LOG_ERROR("Cannot parse UID_DATA.")
                return
        
        stored_fingerprint = fp_match.group(1).strip()
        created_at = datetime.fromisoformat(created_match.group(1).strip())
        expire_text = expiry_match.group(1).strip()
        stored_default = uid_json.get('formats', {}).get('default')
        if not stored_default:
            LOG_ERROR("No default UID found in file.")
            return
        
        if uid_to_verify != stored_default:
            LOG_ERROR("❌ Provided UID does NOT match the stored UID.")
            return
        
        current_fp = device_fingerprint()[:32]
        if stored_fingerprint != current_fp:
            LOG_ERROR("❌ Device fingerprint mismatch.")
            LOG_INFO(f"Stored: {stored_fingerprint}")
            LOG_INFO(f"Current: {current_fp}")
            return
        
        duration = expire_delta_from_text(expire_text)
        expire_date = created_at + duration
        remain = int((expire_date - datetime.now()).total_seconds())
        if remain <= 0:
            LOG_ERROR(f"❌ UID expired on {expire_date.strftime('%Y-%m-%d %H:%M:%S')}")
            return
        
        checksum_str = parts[-1]
        body = '-'.join(parts[:-1])
        computed = zlib.crc32(body.encode()) & 0xFFFFFFFF
        computed_hex = f"{computed:08X}"
        
        LOG_INFO(f"Stored UID      : {stored_default}")
        LOG_INFO(f"Provided UID    : {uid_to_verify}")
        LOG_INFO(f"Body            : {body}")
        LOG_INFO(f"Checksum        : {checksum_str}")
        LOG_INFO(f"Computed        : {computed_hex}")
        
        if checksum_str.upper() == computed_hex:
            LOG_SUCCESS("✅ UID is VALID – matches stored ID, fingerprint, and not expired.")
        else:
            LOG_ERROR("❌ UID checksum mismatch.")
        return
    
    LOG_ERROR("Unknown command. Use --help.")

if __name__ == "__main__":
    main()