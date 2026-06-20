#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# UIDGenerator.py v1.1.1 - ENGLISH VERSION

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
import hmac
import shutil
from datetime import datetime, timedelta

IS_ANDROID = platform.system() == "Android" or "TERMUX" in os.environ.get("TERMUX_VERSION", "")

def is_venv():
    return (hasattr(sys, 'real_prefix') or
            (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix) or
            os.environ.get('VIRTUAL_ENV') is not None)

def install_package(package):
    subprocess.check_call([sys.executable, "-m", "pip", "install", package])

USE_MACHINEID = not IS_ANDROID

def ensure_dependencies():
    required = {
        "cryptography": "cryptography",
        "colorama": "colorama"
    }
    if USE_MACHINEID:
        try:
            importlib.import_module("machineid")
        except ImportError:
            print("[*] Installing py-machineid for better fingerprint...")
            install_package("py-machineid")
            print("[+] py-machineid installed.")
    for module, package in required.items():
        try:
            importlib.import_module(module)
        except ImportError:
            print(f"[*] Installing missing dependency: {package} ...")
            install_package(package)
            print(f"[+] {package} installed.")

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from colorama import Fore, Style, init

init(autoreset=True)

if USE_MACHINEID:
    try:
        import machineid
        MACHINEID_AVAILABLE = True
    except ImportError:
        MACHINEID_AVAILABLE = False
else:
    MACHINEID_AVAILABLE = False

FILE_NAME = "UID.md"
XOR_KEY = 'YkeGCYpccUEgpMyCiWQOLtvcTUgJhDCAchzWrfTsVjrSCNzbjofbeiXxGQRnBVCHviIhOXkJxotiNJtUSBOJuYpBdplNCShnkxtPgaXiNSecuWTGKStLCrOgaDRexrQAHAlGBgCn'
SALT = b'\xc4\x1eP\x88y\x87\x19:\x02\x19\x10<Q\x17J\xcf\xf3\xb0N60u@\xcc\x91<\x88`0\xc7-\xcaY?s:|$\xbc\x84\x90s\xceA\xba\x03\x17\xe5\xd7\xe2f\xfa\t\xb8\x89\xca\x10\x9a\x1dj\xed\xfb\xd9k7\x14\x04\x0c/$_\xe6N7%\x9d1\r\x1e&\xf6BA\xd4z\xff8\xee9\xe4\x06\xd3g\xbbo(\xa1\x10Q\xa7\x93\xe9\x1dt\xc8\xb6:n\x08\xcc(\xba\x97\xa9\x83e\xf5\x8d\x8d\x97\x81\t\xe4\x1f?K\xdd e\xe1\xaf%rQ\xa8x'
VERSION = "1.1.1"

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

if not IS_ANDROID and not is_venv():
    LOG_WARN("You are not inside a virtual environment (venv).")
    LOG_WARN("Dependency installation is cancelled to keep your system clean.")
    LOG_WARN("Create a venv first: python3 -m venv venv && source venv/bin/activate")
    sys.exit(1)

def progress_bar(iteration, total, prefix='', suffix='', decimals=1, length=None, fill='█'):
    try:
        cols = shutil.get_terminal_size().columns
    except:
        cols = 80
    percent = ("{0:." + str(decimals) + "f}").format(100 * (iteration / float(total)))
    elapsed = time.time() - progress_bar._start_time
    if iteration > 0:
        eta = (elapsed / iteration) * (total - iteration)
        eta_str = f"ETA: {eta:.1f}s"
    else:
        eta_str = "ETA: --"
    
    base = f"{prefix} 100.0% {suffix} [{eta_str}]"
    bar_len = cols - len(base) - 4
    if bar_len < 10:
        bar_len = 10
    filled = int(bar_len * iteration / total)
    bar = fill * filled + '-' * (bar_len - filled)
    line = f'\r{prefix} |{bar}| {percent}% {suffix} [{eta_str}]'
    if len(line) > cols:
        available = cols - len(f'\r{prefix} |{bar}| {percent}% ') - 4
        if available < 5:
            suffix = ''
            eta_str = ''
        else:
            if len(suffix) + len(eta_str) + 4 > available:
                max_suffix = available - len(eta_str) - 4
                if max_suffix < 3:
                    suffix = ''
                else:
                    suffix = suffix[:max_suffix-3] + "..."
            line = f'\r{prefix} |{bar}| {percent}% {suffix} [{eta_str}]'
        if len(line) > cols:
            line = f'\r{prefix} |{bar}| {percent}% {suffix}'
            if len(line) > cols:
                max_suffix = cols - len(f'\r{prefix} |{bar}| {percent}% ') - 3
                if max_suffix < 3:
                    suffix = ''
                else:
                    suffix = suffix[:max_suffix-3] + "..."
                line = f'\r{prefix} |{bar}| {percent}% {suffix}'
    line = line.ljust(cols)
    print(line, end='', flush=True)
    if iteration == total:
        print()

progress_bar._start_time = 0

def get_android_prop(prop_name):
    try:
        result = subprocess.check_output(['getprop', prop_name], text=True).strip()
        return result if result else None
    except:
        return None

def device_fingerprint_enhanced() -> str:
    components = []
    if MACHINEID_AVAILABLE:
        try:
            mid = machineid.hashed_id('uid_generator_v12')
            components.append(f"MACHINEID:{mid}")
        except Exception:
            pass
    components.append(f"SYSTEM:{platform.system()}")
    components.append(f"MACHINE:{platform.machine()}")
    components.append(f"ARCH:{platform.architecture()[0]}")
    components.append(f"BITS:{struct.calcsize('P') * 8}")
    components.append(f"CPU:{os.cpu_count()}")
    android_props = ['ro.serialno', 'ro.product.device', 'ro.product.model', 
                     'ro.product.manufacturer', 'ro.build.fingerprint']
    found_android = False
    for prop in android_props:
        val = get_android_prop(prop)
        if val:
            components.append(f"{prop.upper()}:{val}")
            found_android = True
    if not found_android:
        mac = uuid.getnode()
        if mac & 0xFFFFFFFFFFFF:
            components.append(f"MAC:{mac:012X}")
        else:
            components.append("MAC:UNKNOWN")
    try:
        components.append(f"HOST:{socket.gethostname()}")
    except:
        pass
    try:
        components.append(f"USER:{os.getlogin()}")
    except:
        pass
    try:
        if platform.system() == "Windows":
            import winreg
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, 
                r"SYSTEM\CurrentControlSet\Control\Session Manager\Environment")
            val, _ = winreg.QueryValueEx(key, "PROCESSOR_IDENTIFIER")
            components.append(f"PROC:{val}")
    except:
        pass
    components.append(f"TS:{int(time.time() / 86400)}")
    raw = "|".join(components) + "|SALT_UID_V12"
    try:
        return hashlib.sha3_512(raw.encode()).hexdigest()[:64]
    except:
        return hashlib.sha512(raw.encode()).hexdigest()[:64]

def generate_key_from_password(password: str, salt: bytes = None) -> bytes:
    if salt is None:
        salt = SALT
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=150000,
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

def compute_hmac(data: str, key: str = None) -> str:
    if key is None:
        key = XOR_KEY + base64.b64encode(SALT).decode()
    return hmac.new(
        key.encode(),
        data.encode(),
        hashlib.sha256
    ).hexdigest()

def verify_hmac(data: str, signature: str, key: str = None) -> bool:
    expected = compute_hmac(data, key)
    return hmac.compare_digest(expected, signature)

class UIDGenerator:
    def __init__(self):
        self.battlefield_mode = True
        self.generated_ids = set()
        self.fingerprint = device_fingerprint_enhanced()
    
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
        fingerprint = self.fingerprint
        result = {
            "timestamp": timestamp,
            "fingerprint": fingerprint,
            "version": VERSION,
            "formats": {}
        }
        if format_type in ["DEFAULT", "ALL"]:
            uid = self._generate_custom_format(prefix)
            hmac_sig = compute_hmac(uid)
            uid = f"{uid}-{hmac_sig[:8].upper()}"
            result["formats"]["default"] = uid
        if format_type in ["SCRU160", "ALL"]:
            result["formats"]["scru160"] = self._generate_scr160()
        if format_type in ["NANO", "ALL"]:
            result["formats"]["nano"] = self._generate_nanoid()
        if format_type in ["UUID4", "ALL"]:
            result["formats"]["uuid4"] = str(uuid.uuid4()).upper()
        result["fingerprint_binding"] = compute_hmac(
            f"{result['formats'].get('default', '')}|{fingerprint}"
        )
        if self.battlefield_mode:
            for fmt, uid in result["formats"].items():
                if uid in self.generated_ids:
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
        if "years" in unit: return timedelta(days=num*365)
        if "months" in unit: return timedelta(days=num*30)
        if "days" in unit: return timedelta(days=num)
        if "hours" in unit: return timedelta(hours=num)
        if "minutes" in unit: return timedelta(minutes=num)
        if "seconds" in unit: return timedelta(seconds=num)
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
    print(f"  python UIDGenerator.py --create [FORMAT]")
    print(f"  python UIDGenerator.py --check")
    print(f"  python UIDGenerator.py --renew <PWD>")
    print(f"  python UIDGenerator.py --show-password")
    print(f"  python UIDGenerator.py --delete")
    print(f"  python UIDGenerator.py --export")
    print(f"  python UIDGenerator.py --verify <UID>")
    print(f"\n{Fore.CYAN}{BOLD}▶ FORMATS:{RESET} DEFAULT, SCRU160, NANO, UUID4, ALL")
    print(f"\n{Fore.YELLOW}{BOLD}▶ EXAMPLE:{RESET}")
    print(f"  python UIDGenerator.py --create DEFAULT")
    print(color + "-" * BOX_WIDTH + RESET + "\n")

def main():
    args = sys.argv[1:]
    if not args or "--help" in args or "-h" in args:
        show_help()
        return
    
    generator = UIDGenerator()
    
    if args[0] == "--create":
        if os.path.exists(FILE_NAME):
            LOG_WARN("UID already exists. Use --renew.")
            return
        
        format_type = args[1].upper() if len(args) > 1 else "DEFAULT"
        valid_formats = ["DEFAULT", "SCRU160", "NANO", "UUID4", "ALL"]
        if format_type not in valid_formats:
            LOG_ERROR(f"Invalid format! Valid: {', '.join(valid_formats)}")
            return
        
        print(f"\n{Fore.CYAN}{BOLD}CHOOSE TIME UNIT (SECONDS TO YEARS):{RESET}")
        print(f" {Fore.WHITE}1. Seconds   2. Minutes   3. Hours")
        print(f" {Fore.WHITE}4. Days      5. Months    6. Years")
        
        expire_dict = {"years":0, "months":0, "days":0, "hours":0, "minutes":0, "seconds":0}
        try:
            choice = input(f"\n{Fore.WHITE}Enter number (1-6): {Fore.YELLOW}").strip()
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
            LOG_ERROR("Enter a number!")
            return
        
        expire_text = get_expire_text(expire_dict)
        
        uid_data = generator.generate(format_type, prefix="UID")
        raw_password = secrets.token_urlsafe(16)
        encrypted_password = triple_encrypt(raw_password, XOR_KEY)
        uid_json = json.dumps(uid_data)
        data_hmac = compute_hmac(uid_json)
        
        total_steps = 100
        progress_bar._start_time = time.time()
        for i in range(1, total_steps + 1):
            if i < 40:
                suffix = 'Generating UID...'
            elif i < 70:
                suffix = 'Encrypting data...'
            else:
                suffix = 'Saving file...'
            if i == total_steps:
                suffix = 'Done!'
            progress_bar(i, total_steps, prefix='Progress', suffix=suffix, length=None)
            time.sleep(0.015)
        
        with open(FILE_NAME, "w") as f:
            f.write(f"""# UID Information v{VERSION}
# Generated: {uid_data['timestamp']}

UID_DATA : {uid_json}
PASSWORD : {encrypted_password}
FINGERPRINT : {uid_data['fingerprint']}
FINGERPRINT_BINDING : {uid_data.get('fingerprint_binding', 'N/A')}
CREATED_AT : {uid_data['timestamp']}
EXPIRY : {expire_text}
HMAC_SIG : {data_hmac}
""")
        
        LOG_SUCCESS("UID successfully created!")
        print(f"\n{Fore.WHITE}{'═'*60}")
        LOG_INFO(f"UID (default)      : {Fore.YELLOW}{BOLD}{uid_data['formats'].get('default', 'N/A')}")
        LOG_INFO(f"PASSWORD           : {Fore.RED}{BOLD}{raw_password}")
        LOG_INFO(f"EXPIRY             : {Fore.YELLOW}{expire_text}")
        LOG_INFO(f"FINGERPRINT        : {Fore.CYAN}{uid_data['fingerprint']}")
        LOG_INFO(f"HMAC SIGNATURE     : {Fore.MAGENTA}{data_hmac}")
        LOG_INFO(f"FINGERPRINT BINDING: {Fore.BLUE}{uid_data.get('fingerprint_binding', 'N/A')}")
        LOG_INFO(f"CREATED AT         : {Fore.WHITE}{uid_data['timestamp']}")
        LOG_INFO(f"VERSION            : {Fore.GREEN}{VERSION}")
        print(f"{Fore.WHITE}{'═'*60}")
        return
    
    if args[0] == "--check":
        if not os.path.exists(FILE_NAME):
            LOG_ERROR("UID file not found.")
            return
        with open(FILE_NAME, "r") as f:
            content = f.read()
        uid_data_str = re.search(r"UID_DATA\s*:\s*({.*})", content, re.DOTALL)
        fp_str = re.search(r"FINGERPRINT\s*:\s*(\S+)", content)
        fp_binding_str = re.search(r"FINGERPRINT_BINDING\s*:\s*(\S+)", content)
        created_str = re.search(r"CREATED_AT\s*:\s*(\S+)", content)
        expiry_str = re.search(r"EXPIRY\s*:\s*(.+)", content)
        hmac_sig_str = re.search(r"HMAC_SIG\s*:\s*(\S+)", content)
        pwd_enc_str = re.search(r"PASSWORD\s*:\s*(\S+)", content)
        if not uid_data_str or not fp_str or not created_str or not expiry_str:
            LOG_ERROR("UID file corrupted.")
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
                LOG_ERROR("Failed to parse UID_DATA.")
                return
        stored_fingerprint = fp_str.group(1).strip()
        stored_fp_binding = fp_binding_str.group(1).strip() if fp_binding_str else "N/A"
        created_at = datetime.fromisoformat(created_str.group(1).strip())
        expire_text = expiry_str.group(1).strip()
        stored_hmac = hmac_sig_str.group(1).strip() if hmac_sig_str else None
        stored_pwd_enc = pwd_enc_str.group(1).strip() if pwd_enc_str else None
        
        current_fp = device_fingerprint_enhanced()
        valid = True
        
        if stored_fingerprint != current_fp:
            LOG_ERROR("❌ ACCESS DENIED! Fingerprint mismatch.")
            valid = False
        else:
            LOG_SUCCESS("✅ Fingerprint matches.")
        
        if stored_hmac:
            uid_json_str = json.dumps(uid_json)
            if verify_hmac(uid_json_str, stored_hmac):
                LOG_SUCCESS("✅ HMAC-SHA256 integrity valid.")
            else:
                LOG_ERROR("❌ HMAC integrity FAIL! Data tampered.")
                valid = False
        else:
            LOG_WARN("HMAC not found (old version).")
        
        duration = expire_delta_from_text(expire_text)
        expire_date = created_at + duration
        remain = int((expire_date - datetime.now()).total_seconds())
        if remain <= 0:
            LOG_ERROR(f"❌ UID expired on {expire_date.strftime('%Y-%m-%d %H:%M:%S')}")
            valid = False
        else:
            LOG_SUCCESS(f"✅ UID not expired. Remaining: {human_time(remain)}")
        
        print(f"\n{Fore.WHITE}{'═'*60}")
        LOG_INFO(f"UID (default)      : {Fore.YELLOW}{BOLD}{uid_json.get('formats', {}).get('default', 'N/A')}")
        LOG_INFO(f"PASSWORD (enc)     : {Fore.RED}{stored_pwd_enc if stored_pwd_enc else 'N/A'}")
        LOG_INFO(f"EXPIRY             : {Fore.YELLOW}{expire_text}")
        LOG_INFO(f"FINGERPRINT        : {Fore.CYAN}{stored_fingerprint}")
        LOG_INFO(f"HMAC SIGNATURE     : {Fore.MAGENTA}{stored_hmac if stored_hmac else 'N/A'}")
        LOG_INFO(f"FINGERPRINT BINDING: {Fore.BLUE}{stored_fp_binding}")
        LOG_INFO(f"CREATED AT         : {Fore.WHITE}{created_at.isoformat()}")
        LOG_INFO(f"VERSION            : {Fore.GREEN}{uid_json.get('version', 'N/A')}")
        LOG_INFO(f"STATUS             : {Fore.GREEN if valid else Fore.RED}{'VALID' if valid else 'INVALID'}")
        print(f"{Fore.WHITE}{'═'*60}")
        return
    
    if args[0] == "--show-password":
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
            decrypted = triple_decrypt(encrypted, XOR_KEY)
            LOG_INFO(f"Password: {Fore.RED}{BOLD}{decrypted}")
        except:
            LOG_ERROR("Failed to decrypt password.")
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
        uid_json = None
        for line in lines:
            if line.strip().startswith("CREATED_AT"):
                new_lines.append(f"CREATED_AT : {datetime.now().isoformat()}")
            elif line.strip().startswith("EXPIRY"):
                new_lines.append(f"EXPIRY : {expire_text}")
            elif line.strip().startswith("UID_DATA"):
                raw_json = line.split(":", 1)[1].strip()
                try:
                    uid_json = json.loads(raw_json)
                    uid_json['timestamp'] = datetime.now().isoformat()
                    new_uid_json = json.dumps(uid_json)
                    new_lines.append(f"UID_DATA : {new_uid_json}")
                    new_hmac = compute_hmac(new_uid_json)
                except:
                    new_lines.append(line)
            elif line.strip().startswith("HMAC_SIG"):
                if uid_json:
                    new_uid_json = json.dumps(uid_json)
                    new_hmac = compute_hmac(new_uid_json)
                    new_lines.append(f"HMAC_SIG : {new_hmac}")
                else:
                    new_lines.append(line)
            elif line.strip().startswith("FINGERPRINT_BINDING"):
                if uid_json:
                    default_uid = uid_json.get('formats', {}).get('default', '')
                    fp = device_fingerprint_enhanced()
                    new_binding = compute_hmac(f"{default_uid}|{fp}")
                    new_lines.append(f"FINGERPRINT_BINDING : {new_binding}")
                else:
                    new_lines.append(line)
            else:
                new_lines.append(line)
        with open(FILE_NAME, "w") as f:
            f.write("\n".join(new_lines))
        LOG_SUCCESS("UID renewed successfully!")
        LOG_INFO(f"New CREATED_AT: {datetime.now().isoformat()}")
        LOG_INFO(f"Expiry unchanged: {expire_text}")
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
        LOG_SUCCESS("Exported to uid_export.json.")
        return
    
    if args[0] == "--verify" and len(args) > 1:
        uid_to_verify = args[1].strip()
        
        if not os.path.exists(FILE_NAME):
            LOG_ERROR("UID file not found.")
            return
        with open(FILE_NAME, "r") as f:
            content = f.read()
        uid_data_str = re.search(r"UID_DATA\s*:\s*({.*})", content, re.DOTALL)
        fp_match = re.search(r"FINGERPRINT\s*:\s*(\S+)", content)
        fp_binding_str = re.search(r"FINGERPRINT_BINDING\s*:\s*(\S+)", content)
        created_match = re.search(r"CREATED_AT\s*:\s*(\S+)", content)
        expiry_match = re.search(r"EXPIRY\s*:\s*(.+)", content)
        hmac_sig_match = re.search(r"HMAC_SIG\s*:\s*(\S+)", content)
        pwd_enc_str = re.search(r"PASSWORD\s*:\s*(\S+)", content)
        if not uid_data_str or not fp_match or not created_match or not expiry_match:
            LOG_ERROR("UID file corrupted.")
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
                LOG_ERROR("Failed to parse UID_DATA.")
                return
        
        stored_fingerprint = fp_match.group(1).strip()
        stored_fp_binding = fp_binding_str.group(1).strip() if fp_binding_str else "N/A"
        created_at = datetime.fromisoformat(created_match.group(1).strip())
        expire_text = expiry_match.group(1).strip()
        stored_hmac = hmac_sig_match.group(1).strip() if hmac_sig_match else None
        stored_pwd_enc = pwd_enc_str.group(1).strip() if pwd_enc_str else None
        
        stored_ids = list(uid_json.get('formats', {}).values())
        if uid_to_verify not in stored_ids:
            LOG_ERROR("❌ UID does not match any stored format.")
            return
        
        current_fp = device_fingerprint_enhanced()
        if stored_fingerprint != current_fp:
            LOG_ERROR("❌ Fingerprint mismatch.")
            return
        
        if stored_hmac:
            uid_json_str = json.dumps(uid_json)
            if not verify_hmac(uid_json_str, stored_hmac):
                LOG_ERROR("❌ HMAC integrity FAIL.")
                return
        
        duration = expire_delta_from_text(expire_text)
        expire_date = created_at + duration
        remain = int((expire_date - datetime.now()).total_seconds())
        if remain <= 0:
            LOG_ERROR(f"❌ UID expired on {expire_date.strftime('%Y-%m-%d %H:%M:%S')}")
            return
        
        if uid_to_verify == uid_json.get('formats', {}).get('default'):
            if '-' in uid_to_verify:
                parts = uid_to_verify.split('-')
                if len(parts) >= 2:
                    body = '-'.join(parts[:-1])
                    hmac_part = parts[-1]
                    computed_hmac = compute_hmac(body)[:8].upper()
                    if hmac_part.upper() != computed_hmac:
                        LOG_ERROR("❌ UID HMAC checksum mismatch.")
                        return
            else:
                LOG_ERROR("❌ Default format must have hyphens for checksum.")
                return
        
        LOG_SUCCESS("✅ UID VALID – all verifications passed!")
        print(f"\n{Fore.WHITE}{'═'*60}")
        LOG_INFO(f"UID (default)      : {Fore.YELLOW}{BOLD}{uid_json.get('formats', {}).get('default', 'N/A')}")
        LOG_INFO(f"PASSWORD (enc)     : {Fore.RED}{stored_pwd_enc if stored_pwd_enc else 'N/A'}")
        LOG_INFO(f"EXPIRY             : {Fore.YELLOW}{expire_text}")
        LOG_INFO(f"FINGERPRINT        : {Fore.CYAN}{stored_fingerprint}")
        LOG_INFO(f"HMAC SIGNATURE     : {Fore.MAGENTA}{stored_hmac if stored_hmac else 'N/A'}")
        LOG_INFO(f"FINGERPRINT BINDING: {Fore.BLUE}{stored_fp_binding}")
        LOG_INFO(f"CREATED AT         : {Fore.WHITE}{created_at.isoformat()}")
        LOG_INFO(f"VERSION            : {Fore.GREEN}{uid_json.get('version', 'N/A')}")
        LOG_INFO(f"STATUS             : {Fore.GREEN}VALID (verified)")
        for fmt, uid in uid_json.get('formats', {}).items():
            if fmt != 'default':
                LOG_INFO(f"FORMAT {fmt.upper():<10} : {Fore.YELLOW}{uid}")
        print(f"{Fore.WHITE}{'═'*60}")
        return
    
    LOG_ERROR("Unknown command. Use --help.")

if __name__ == "__main__":
    ensure_dependencies()
    main()