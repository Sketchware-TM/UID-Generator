#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# UIDGenerator.py v1.1.1 - INDONESIAN VERSION

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

def install_package(package):
    subprocess.check_call([sys.executable, "-m", "pip", "install", package])

# Deteksi OS
IS_ANDROID = platform.system() == "Android" or "TERMUX" in os.environ.get("TERMUX_VERSION", "")
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

ensure_dependencies()

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from colorama import Fore, Style, init

init(autoreset=True)

# Import machineid hanya jika diizinkan
if USE_MACHINEID:
    try:
        import machineid
        MACHINEID_AVAILABLE = True
    except ImportError:
        MACHINEID_AVAILABLE = False
else:
    MACHINEID_AVAILABLE = False

FILE_NAME = "UID.md"
XOR_KEY = "lSoXWboNRdUsgOtzGdBbJxaoBdvGmYDWvjvZxzxIFoCFsfEUryLXnjDomACMGNIC"
SALT = b'\x05-\x17\x89h\xed\xb8\x9bM6m\x97_\xe3\x1auI\x91\xff\x81\x0can\x08\xc8G&\xcc^4\xb0-\xdaO;\x08w\xf6\xf80\xac\xd1a!1\xae~g\xed-W"\xad\xfb$\x08\xe5y:\xd4\xad\xa6\xb6\x07'
VERSION = "1.1.1"  # TETAP

BOLD = Style.BRIGHT
RESET = Style.RESET_ALL

def LOG_INFO(msg):
    print(f"{Fore.CYAN}{BOLD}[INFO]{RESET} {BOLD}{msg}{RESET}")

def LOG_WARN(msg):
    print(f"{Fore.YELLOW}{BOLD}[WARNING]{RESET} {Fore.YELLOW}{BOLD}{msg}{RESET}")

def LOG_ERROR(msg):
    print(f"{Fore.RED}{BOLD}[ERROR]{RESET} {Fore.RED}{BOLD}{msg}{RESET}")

def LOG_SUCCESS(msg):
    print(f"{Fore.GREEN}{BOLD}[SUKSES]{RESET} {Fore.GREEN}{BOLD}{msg}{RESET}")

# ============= PROGRESS BAR (SATU BARIS + TRUNCATE) =============
def progress_bar(iteration, total, prefix='', suffix='', decimals=1, length=None, fill='█', print_end="\r"):
    # Ambil lebar terminal
    try:
        cols = shutil.get_terminal_size().columns
    except:
        cols = 80
    # Build the line components
    percent = ("{0:." + str(decimals) + "f}").format(100 * (iteration / float(total)))
    elapsed = time.time() - progress_bar._start_time
    if iteration > 0:
        eta = (elapsed / iteration) * (total - iteration)
        eta_str = f"ETA: {eta:.1f}s"
    else:
        eta_str = "ETA: --"
    # Bar length: at least 10, but reduce if total line too long
    if length is None:
        # Estimate lengths of other parts
        prefix_len = len(prefix) + 2  # +2 for spaces
        suffix_len = len(suffix) + len(eta_str) + 8  # percent, brackets, etc.
        max_bar_len = cols - prefix_len - suffix_len - 5  # -5 for safety
        length = max(10, max_bar_len)
    filled_length = int(length * iteration // total)
    bar = fill * filled_length + '-' * (length - filled_length)
    # Construct the line
    line = f'\r{prefix} |{bar}| {percent}% {suffix} [{eta_str}]'
    # If line longer than terminal columns, truncate suffix
    if len(line) > cols:
        # Truncate suffix: keep prefix + bar + percent, then add "..." + eta
        # But we need to keep eta if possible
        # Let's shorten suffix
        max_suffix_len = cols - len(f'\r{prefix} |{bar}| {percent}% ') - 4  # for "[...]"
        if max_suffix_len < 5:
            # Too narrow, just show minimal
            line = f'\r{prefix} |{bar}| {percent}% ...'
        else:
            if len(suffix) > max_suffix_len:
                suffix = suffix[:max_suffix_len-3] + "..."
            line = f'\r{prefix} |{bar}| {percent}% {suffix} [{eta_str}]'
            # If still too long, remove eta
            if len(line) > cols:
                line = f'\r{prefix} |{bar}| {percent}% {suffix} ...'
    print(line, end=print_end, flush=True)
    if iteration == total:
        print()  # newline after finish

progress_bar._start_time = 0

# ============= ENHANCED DEVICE FINGERPRINT (silent) =============
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

# ============= CRYPTO CORE =============
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

# ============= HMAC-SHA256 (internal) =============
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

# ============= UID GENERATOR CORE =============
class UIDGenerator:
    def __init__(self):
        self.battlefield_mode = True
        self.generated_ids = set()
        self.fingerprint = device_fingerprint_enhanced()
        # Gak print fingerprint di sini
    
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

# ============= UTILITY =============
def get_expire_text(expire_dict):
    parts = []
    name_map = {
        "years": "Tahun",
        "months": "Bulan",
        "days": "Hari",
        "hours": "Jam",
        "minutes": "Menit",
        "seconds": "Detik"
    }
    for unit, value in expire_dict.items():
        if value > 0:
            parts.append(f"{value} {name_map.get(unit, unit)}")
    return ", ".join(parts) if parts else "0 Detik"

def expire_delta_from_text(expire_text):
    try:
        parts = expire_text.split()
        num = int(parts[0])
        unit = parts[1].lower()
        if "tahun" in unit: return timedelta(days=num*365)
        if "bulan" in unit: return timedelta(days=num*30)
        if "hari" in unit: return timedelta(days=num)
        if "jam" in unit: return timedelta(hours=num)
        if "menit" in unit: return timedelta(minutes=num)
        if "detik" in unit: return timedelta(seconds=num)
    except:
        pass
    return timedelta(days=365)

def human_time(seconds):
    units = [("Tahun", 31536000), ("Bulan", 2592000), ("Hari", 86400),
             ("Jam", 3600), ("Menit", 60), ("Detik", 1)]
    out = []
    for name, size in units:
        val, seconds = divmod(seconds, size)
        if val:
            out.append(f"{val} {name}")
    return " ".join(out) or "0 Detik"

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
    print(f"\n{Fore.GREEN}{BOLD}▶ PERINTAH:{RESET}")
    print(f"  python UIDGenerator.py --create [FORMAT]")
    print(f"  python UIDGenerator.py --check")
    print(f"  python UIDGenerator.py --renew <PWD>")
    print(f"  python UIDGenerator.py --show-password")
    print(f"  python UIDGenerator.py --delete")
    print(f"  python UIDGenerator.py --export")
    print(f"  python UIDGenerator.py --verify <UID>")
    print(f"\n{Fore.CYAN}{BOLD}▶ FORMAT:{RESET} DEFAULT, SCRU160, NANO, UUID4, ALL")
    print(f"\n{Fore.YELLOW}{BOLD}▶ CONTOH:{RESET}")
    print(f"  python UIDGenerator.py --create DEFAULT")
    print(color + "-" * BOX_WIDTH + RESET + "\n")

# ============= MAIN =============
def main():
    args = sys.argv[1:]
    if not args or "--help" in args or "-h" in args:
        show_help()
        return
    
    generator = UIDGenerator()
    
    if args[0] == "--create":
        if os.path.exists(FILE_NAME):
            LOG_WARN("UID udah ada. Pake --renew.")
            return
        
        format_type = args[1].upper() if len(args) > 1 else "DEFAULT"
        valid_formats = ["DEFAULT", "SCRU160", "NANO", "UUID4", "ALL"]
        if format_type not in valid_formats:
            LOG_ERROR(f"Format gak valid! Pakenya: {', '.join(valid_formats)}")
            return
        
        print(f"\n{Fore.CYAN}{BOLD}PILIH SATUAN WAKTU (DETIK SAMPAI TAHUN):{RESET}")
        print(f" {Fore.WHITE}1. Detik   2. Menit   3. Jam")
        print(f" {Fore.WHITE}4. Hari    5. Bulan   6. Tahun")
        
        expire_dict = {"years":0, "months":0, "days":0, "hours":0, "minutes":0, "seconds":0}
        try:
            choice = input(f"\n{Fore.WHITE}Masukin nomor (1-6): {Fore.YELLOW}").strip()
            unit_map = {
                "1": "seconds", "2": "minutes", "3": "hours",
                "4": "days", "5": "months", "6": "years"
            }
            display_map = {
                "1": "Detik", "2": "Menit", "3": "Jam",
                "4": "Hari", "5": "Bulan", "6": "Tahun"
            }
            if choice in unit_map:
                unit_key = unit_map[choice]
                unit_display = display_map[choice]
                amount_input = input(f"{Fore.WHITE}Masukin jumlah {Fore.CYAN}{unit_display}{Fore.WHITE} (Default 1): {Fore.YELLOW}").strip()
                amount = int(amount_input) if amount_input != "" else 1
                if amount <= 0:
                    LOG_ERROR("Jumlahnya harus positif!")
                    return
                expire_dict[unit_key] = amount
            else:
                LOG_ERROR("Pilihan salah!")
                return
        except ValueError:
            LOG_ERROR("Masukin angka aja!")
            return
        
        expire_text = get_expire_text(expire_dict)
        
        # === PROGRESS BAR (SATU BARIS) ===
        total_steps = 100
        progress_bar._start_time = time.time()
        
        # Tahap 1: Generate UID
        for i in range(1, 40):
            progress_bar(i, total_steps, prefix='Progress', suffix='Generating UID...', length=None)
            time.sleep(0.015)
        uid_data = generator.generate(format_type, prefix="UID")
        
        # Tahap 2: Encrypt
        for i in range(40, 70):
            progress_bar(i, total_steps, prefix='Progress', suffix='Encrypting data...', length=None)
            time.sleep(0.015)
        raw_password = secrets.token_urlsafe(16)
        encrypted_password = triple_encrypt(raw_password, XOR_KEY)
        
        # Tahap 3: Save file
        uid_json = json.dumps(uid_data)
        data_hmac = compute_hmac(uid_json)
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
        for i in range(70, 101):
            progress_bar(i, total_steps, prefix='Progress', suffix='Saving file...', length=None)
            time.sleep(0.015)
        progress_bar(total_steps, total_steps, prefix='Progress', suffix='Selesai!', length=None)
        
        LOG_SUCCESS("UID berhasil dibuat!")
        print(f"\n{Fore.WHITE}{'═'*60}")
        LOG_INFO(f"UID (default)      : {Fore.YELLOW}{BOLD}{uid_data['formats'].get('default', 'N/A')}")
        LOG_INFO(f"PASSWORD           : {Fore.RED}{BOLD}{raw_password}")
        LOG_INFO(f"KEDALUWARSA        : {Fore.YELLOW}{expire_text}")
        LOG_INFO(f"FINGERPRINT        : {Fore.CYAN}{uid_data['fingerprint']}")
        LOG_INFO(f"HMAC SIGNATURE     : {Fore.MAGENTA}{data_hmac}")
        LOG_INFO(f"FINGERPRINT BINDING: {Fore.BLUE}{uid_data.get('fingerprint_binding', 'N/A')}")
        LOG_INFO(f"CREATED AT         : {Fore.WHITE}{uid_data['timestamp']}")
        LOG_INFO(f"VERSION            : {Fore.GREEN}{VERSION}")
        print(f"{Fore.WHITE}{'═'*60}")
        return
    
    # ============= PERINTAH --check (tampilkan semua info) =============
    if args[0] == "--check":
        if not os.path.exists(FILE_NAME):
            LOG_ERROR("UID gak ketemu.")
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
            LOG_ERROR("File UID rusak.")
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
                LOG_ERROR("Gak bisa parsing UID_DATA.")
                return
        stored_fingerprint = fp_str.group(1).strip()
        stored_fp_binding = fp_binding_str.group(1).strip() if fp_binding_str else "N/A"
        created_at = datetime.fromisoformat(created_str.group(1).strip())
        expire_text = expiry_str.group(1).strip()
        stored_hmac = hmac_sig_str.group(1).strip() if hmac_sig_str else None
        stored_pwd_enc = pwd_enc_str.group(1).strip() if pwd_enc_str else None
        
        current_fp = device_fingerprint_enhanced()
        valid = True
        
        # Verifikasi fingerprint
        if stored_fingerprint != current_fp:
            LOG_ERROR("❌ AKSES DITOLAK! Fingerprint berbeda.")
            valid = False
        else:
            LOG_SUCCESS("✅ Fingerprint cocok.")
        
        # Verifikasi HMAC
        if stored_hmac:
            uid_json_str = json.dumps(uid_json)
            if verify_hmac(uid_json_str, stored_hmac):
                LOG_SUCCESS("✅ HMAC-SHA256 integrity VALID.")
            else:
                LOG_ERROR("❌ HMAC integrity FAIL! Data diubah.")
                valid = False
        else:
            LOG_WARN("HMAC tidak ditemukan (versi lama).")
        
        # Cek kedaluwarsa
        duration = expire_delta_from_text(expire_text)
        expire_date = created_at + duration
        remain = int((expire_date - datetime.now()).total_seconds())
        if remain <= 0:
            LOG_ERROR(f"❌ UID kadaluwarsa pada {expire_date.strftime('%Y-%m-%d %H:%M:%S')}")
            valid = False
        else:
            LOG_SUCCESS(f"✅ UID belum expired. Sisa {human_time(remain)}")
        
        # Tampilkan semua info (termasuk UID dari file)
        print(f"\n{Fore.WHITE}{'═'*60}")
        LOG_INFO(f"UID (default)      : {Fore.YELLOW}{BOLD}{uid_json.get('formats', {}).get('default', 'N/A')}")
        LOG_INFO(f"PASSWORD (enc)     : {Fore.RED}{stored_pwd_enc if stored_pwd_enc else 'N/A'}")
        LOG_INFO(f"KEDALUWARSA        : {Fore.YELLOW}{expire_text}")
        LOG_INFO(f"FINGERPRINT        : {Fore.CYAN}{stored_fingerprint}")
        LOG_INFO(f"HMAC SIGNATURE     : {Fore.MAGENTA}{stored_hmac if stored_hmac else 'N/A'}")
        LOG_INFO(f"FINGERPRINT BINDING: {Fore.BLUE}{stored_fp_binding}")
        LOG_INFO(f"CREATED AT         : {Fore.WHITE}{created_at.isoformat()}")
        LOG_INFO(f"VERSION            : {Fore.GREEN}{uid_json.get('version', 'N/A')}")
        LOG_INFO(f"STATUS             : {Fore.GREEN if valid else Fore.RED}{'VALID' if valid else 'INVALID'}")
        print(f"{Fore.WHITE}{'═'*60}")
        return
    
    # ============= PERINTAH LAIN (tetep) =============
    if args[0] == "--show-password":
        if not os.path.exists(FILE_NAME):
            LOG_ERROR("File gak ada.")
            return
        with open(FILE_NAME, "r") as f:
            content = f.read()
        pwd_match = re.search(r"PASSWORD\s*:\s*(\S+)", content)
        if not pwd_match:
            LOG_ERROR("Password gak ketemu.")
            return
        encrypted = pwd_match.group(1).strip()
        try:
            decrypted = triple_decrypt(encrypted, XOR_KEY)
            LOG_INFO(f"Password: {Fore.RED}{BOLD}{decrypted}")
        except:
            LOG_ERROR("Gagal dekripsi password.")
        return
    
    if args[0] == "--renew" and len(args) > 1:
        provided_pwd = args[1]
        if not os.path.exists(FILE_NAME):
            LOG_ERROR("File gak ada.")
            return
        with open(FILE_NAME, "r") as f:
            content = f.read()
        pwd_match = re.search(r"PASSWORD\s*:\s*(\S+)", content)
        if not pwd_match:
            LOG_ERROR("Password gak ketemu.")
            return
        encrypted = pwd_match.group(1).strip()
        try:
            stored_pwd = triple_decrypt(encrypted, XOR_KEY)
            if provided_pwd != stored_pwd:
                LOG_ERROR("Password salah!")
                return
        except:
            LOG_ERROR("Gagal verifikasi password.")
            return
        expiry_match = re.search(r"EXPIRY\s*:\s*(.+)", content)
        if not expiry_match:
            LOG_ERROR("Kedaluwarsa gak ketemu.")
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
        LOG_SUCCESS("UID diperpanjang!")
        LOG_INFO(f"CREATED_AT baru: {datetime.now().isoformat()}")
        LOG_INFO(f"Kedaluwarsa: {expire_text}")
        return
    
    if args[0] == "--delete":
        if os.path.exists(FILE_NAME):
            os.remove(FILE_NAME)
            LOG_SUCCESS("UID dihapus.")
        else:
            LOG_WARN("Gak ada UID.")
        return
    
    if args[0] == "--export":
        if not os.path.exists(FILE_NAME):
            LOG_ERROR("File gak ada.")
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
        LOG_SUCCESS("Ekspor ke uid_export.json.")
        return
    
    if args[0] == "--verify" and len(args) > 1:
        uid_to_verify = args[1].strip()
        if '-' not in uid_to_verify:
            LOG_ERROR("Format UID salah.")
            return
        parts = uid_to_verify.split('-')
        if len(parts) < 2:
            LOG_ERROR("Format UID kurang tepat.")
            return
        if not os.path.exists(FILE_NAME):
            LOG_ERROR("File UID gak ada.")
            return
        with open(FILE_NAME, "r") as f:
            content = f.read()
        uid_data_str = re.search(r"UID_DATA\s*:\s*({.*})", content, re.DOTALL)
        fp_match = re.search(r"FINGERPRINT\s*:\s*(\S+)", content)
        created_match = re.search(r"CREATED_AT\s*:\s*(\S+)", content)
        expiry_match = re.search(r"EXPIRY\s*:\s*(.+)", content)
        hmac_sig_match = re.search(r"HMAC_SIG\s*:\s*(\S+)", content)
        if not uid_data_str or not fp_match or not created_match or not expiry_match:
            LOG_ERROR("File UID rusak.")
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
                LOG_ERROR("Gak bisa parsing UID_DATA.")
                return
        stored_fingerprint = fp_match.group(1).strip()
        created_at = datetime.fromisoformat(created_match.group(1).strip())
        expire_text = expiry_match.group(1).strip()
        stored_default = uid_json.get('formats', {}).get('default')
        stored_hmac = hmac_sig_match.group(1).strip() if hmac_sig_match else None
        if not stored_default:
            LOG_ERROR("Gak ada UID default.")
            return
        if uid_to_verify != stored_default:
            LOG_ERROR("❌ UID gak cocok.")
            return
        current_fp = device_fingerprint_enhanced()
        if stored_fingerprint != current_fp:
            LOG_ERROR("❌ Fingerprint berbeda.")
            return
        if stored_hmac:
            uid_json_str = json.dumps(uid_json)
            if not verify_hmac(uid_json_str, stored_hmac):
                LOG_ERROR("❌ HMAC integrity FAIL.")
                return
        body = '-'.join(parts[:-1])
        hmac_part = parts[-1]
        computed_hmac = compute_hmac(body)[:8].upper()
        if hmac_part.upper() == computed_hmac:
            LOG_SUCCESS("✅ UID VALID.")
        else:
            LOG_ERROR("❌ HMAC UID gak cocok.")
        return
    
    LOG_ERROR("Perintah gak dikenal. Pake --help.")

if __name__ == "__main__":
    main()