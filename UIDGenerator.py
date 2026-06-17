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
            print(f"[*] Lagi install dependensi yang hilang: {package} ...")
            install_package(package)
            print(f"[+] {package} udah keinstall coy.")

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
    print(f"{Fore.GREEN}{BOLD}[SUKSES]{RESET} {Fore.GREEN}{BOLD}{msg}{RESET}")

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
                    LOG_WARN(f"Waduh, tabrakan di {fmt}! Lagi generate ulang...")
                    return self.generate(format_type, prefix)
                self.generated_ids.add(uid)
        
        return result

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

    print(f"\n{Fore.GREEN}{BOLD}▶ PERINTAH YANG BISA DIPAKE:{RESET}")
    print(f"  python UIDGenerator.py --create [FORMAT]    Buat UID baru")
    print(f"  python UIDGenerator.py --check              Cek status UID")
    print(f"  python UIDGenerator.py --renew <PWD>        Perpanjang masa berlaku UID")
    print(f"  python UIDGenerator.py --show-password      Tampilin password")
    print(f"  python UIDGenerator.py --delete             Hapus file UID")
    print(f"  python UIDGenerator.py --export             Ekspor ke JSON")
    print(f"  python UIDGenerator.py --verify <UID>       Verifikasi UID yang udah dibuat")
    
    print(f"\n{Fore.CYAN}{BOLD}▶ FORMAT ID:{RESET}")
    print(f"  DEFAULT   : XX-XXXX-XXXX-XXXX-XXXX-XXXX-XXXXXXXX (pake checksum)")
    print(f"  SCRU160   : 32 karakter base32hex (bisa diurutin berdasarkan waktu)")
    print(f"  NANO      : ID aman kripto yang ramah URL")
    print(f"  UUID4     : UUID4 standar")
    print(f"  ALL       : Hasilin semua format sekaligus")
    
    print(f"\n{Fore.YELLOW}{BOLD}▶ CONTOH PAKE:{RESET}")
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
            LOG_WARN("UID udah ada bang. Pake --renew kalo mau perpanjang.")
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
                    LOG_ERROR("Jumlahnya harus positif dong!")
                    return
                expire_dict[unit_key] = amount
            else:
                LOG_ERROR("Pilihan salah bre!")
                return
        except ValueError:
            LOG_ERROR("Yang bener masukin angka aja!")
            return
        
        expire_text = get_expire_text(expire_dict)
        LOG_INFO(f"Kedaluwarsa diatur ke: {expire_text}")
        
        LOG_INFO(f"Lagi generate UID {format_type}...")
        
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
        
        LOG_SUCCESS("UID berhasil dibuat!")
        print(f"\n{Fore.WHITE}{'═'*60}")
        LOG_INFO(f"UID (default) : {Fore.YELLOW}{BOLD}{uid_data['formats'].get('default', 'N/A')}")
        LOG_INFO(f"SCRU160      : {Fore.YELLOW}{BOLD}{uid_data['formats'].get('scru160', 'N/A')}")
        LOG_INFO(f"NANO ID      : {Fore.YELLOW}{BOLD}{uid_data['formats'].get('nano', 'N/A')}")
        LOG_INFO(f"PASSWORD     : {Fore.RED}{BOLD}{raw_password}")
        LOG_INFO(f"FINGERPRINT  : {Fore.CYAN}{uid_data['fingerprint'][:16]}...")
        LOG_INFO(f"KEDALUWARSA  : {Fore.YELLOW}{expire_text}")
        print(f"{Fore.WHITE}{'═'*60}")
        return
    
    if args[0] == "--check":
        if not os.path.exists(FILE_NAME):
            LOG_ERROR("UID gak ketemu. Buat dulu pake --create.")
            return
        
        with open(FILE_NAME, "r") as f:
            content = f.read()
        
        uid_data_str = re.search(r"UID_DATA\s*:\s*({.*})", content, re.DOTALL)
        fp_str = re.search(r"FINGERPRINT\s*:\s*(\S+)", content)
        created_str = re.search(r"CREATED_AT\s*:\s*(\S+)", content)
        expiry_str = re.search(r"EXPIRY\s*:\s*(.+)", content)
        
        if not uid_data_str or not fp_str or not created_str or not expiry_str:
            LOG_ERROR("File UID rusak njir.")
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
        created_at = datetime.fromisoformat(created_str.group(1).strip())
        expire_text = expiry_str.group(1).strip()
        
        current_fp = device_fingerprint()[:32]
        if stored_fingerprint != current_fp:
            LOG_ERROR("Akses ditolak! Sidik jari perangkat beda.")
            LOG_INFO(f"Yang tersimpan: {stored_fingerprint}")
            LOG_INFO(f"Yang sekarang: {current_fp}")
            return
        
        duration = expire_delta_from_text(expire_text)
        expire_date = created_at + duration
        remain = int((expire_date - datetime.now()).total_seconds())
        
        if remain <= 0:
            LOG_ERROR(f"UID udah kadaluwarsa nih pada {expire_date.strftime('%Y-%m-%d %H:%M:%S')}")
        else:
            LOG_SUCCESS("UID valid mantap.")
            LOG_INFO(f"Sisa waktu: {Fore.GREEN}{human_time(remain)}")
            LOG_INFO(f"Kadaluwarsa: {expire_date.strftime('%Y-%m-%d %H:%M:%S')}")
        return
    
    if args[0] == "--show-password":
        if not os.path.exists(FILE_NAME):
            LOG_ERROR("File gak ada.")
            return
        
        with open(FILE_NAME, "r") as f:
            content = f.read()
        
        pwd_match = re.search(r"PASSWORD\s*:\s*(\S+)", content)
        if not pwd_match:
            LOG_ERROR("Password gak ketemu di file.")
            return
        encrypted = pwd_match.group(1).strip()
        try:
            decrypted = triple_decrypt(encrypted, XOR_KEY)
            LOG_INFO(f"Password: {Fore.RED}{BOLD}{decrypted}")
        except Exception as e:
            LOG_ERROR("Gagal mendekripsi password.")
            LOG_INFO("Mungkin ini karena pake versi lama yang salt-nya acak.")
            LOG_INFO("Coba hapus UID.md trus bikin ulang pake versi ini.")
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
        for line in lines:
            if line.strip().startswith("CREATED_AT"):
                new_lines.append(f"CREATED_AT : {datetime.now().isoformat()}")
            elif line.strip().startswith("EXPIRY"):
                new_lines.append(f"EXPIRY : {expire_text}")
            else:
                new_lines.append(line)
        
        with open(FILE_NAME, "w") as f:
            f.write("\n".join(new_lines))
        
        LOG_SUCCESS("UID berhasil diperpanjang!")
        LOG_INFO(f"CREATED_AT baru: {datetime.now().isoformat()}")
        LOG_INFO(f"Kedaluwarsa tetep: {expire_text}")
        return
    
    if args[0] == "--delete":
        if os.path.exists(FILE_NAME):
            os.remove(FILE_NAME)
            LOG_SUCCESS("UID udah dihapus.")
        else:
            LOG_WARN("Gak ada UID yang mau dihapus.")
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
        
        LOG_SUCCESS("Ekspor ke uid_export.json sukses.")
        return
    
    if args[0] == "--verify" and len(args) > 1:
        uid_to_verify = args[1].strip()
        
        if '-' not in uid_to_verify:
            LOG_ERROR("Format UID salah. Harus pake tanda hubung.")
            return
        parts = uid_to_verify.split('-')
        if len(parts) < 2:
            LOG_ERROR("Format UID kurang tepat. Minimal dua bagian.")
            return
        
        if not os.path.exists(FILE_NAME):
            LOG_ERROR("File UID gak ada. Gak bisa verifikasi.")
            return
        
        with open(FILE_NAME, "r") as f:
            content = f.read()
        
        uid_data_str = re.search(r"UID_DATA\s*:\s*({.*})", content, re.DOTALL)
        fp_match = re.search(r"FINGERPRINT\s*:\s*(\S+)", content)
        created_match = re.search(r"CREATED_AT\s*:\s*(\S+)", content)
        expiry_match = re.search(r"EXPIRY\s*:\s*(.+)", content)
        
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
        if not stored_default:
            LOG_ERROR("Gak ada UID default di file.")
            return
        
        if uid_to_verify != stored_default:
            LOG_ERROR("❌ UID yang lu kasih GAK cocok sama yang tersimpan.")
            return
        
        current_fp = device_fingerprint()[:32]
        if stored_fingerprint != current_fp:
            LOG_ERROR("❌ Sidik jari perangkat beda.")
            LOG_INFO(f"Tersimpan: {stored_fingerprint}")
            LOG_INFO(f"Sekarang: {current_fp}")
            return
        
        duration = expire_delta_from_text(expire_text)
        expire_date = created_at + duration
        remain = int((expire_date - datetime.now()).total_seconds())
        if remain <= 0:
            LOG_ERROR(f"❌ UID udah kadaluwarsa pada {expire_date.strftime('%Y-%m-%d %H:%M:%S')}")
            return
        
        checksum_str = parts[-1]
        body = '-'.join(parts[:-1])
        computed = zlib.crc32(body.encode()) & 0xFFFFFFFF
        computed_hex = f"{computed:08X}"
        
        LOG_INFO(f"UID tersimpan   : {stored_default}")
        LOG_INFO(f"UID yang lu kasih: {uid_to_verify}")
        LOG_INFO(f"Badan           : {body}")
        LOG_INFO(f"Checksum        : {checksum_str}")
        LOG_INFO(f"Hasil hitung    : {computed_hex}")
        
        if checksum_str.upper() == computed_hex:
            LOG_SUCCESS("✅ UID VALID – cocok sama ID tersimpan, sidik jari, dan belum kadaluwarsa.")
        else:
            LOG_ERROR("❌ Checksum UID gak cocok.")
        return
    
    LOG_ERROR("Perintah gak dikenal. Pake --help.")

if __name__ == "__main__":
    main()