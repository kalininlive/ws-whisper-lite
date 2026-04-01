import json
import os
import base64

CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "settings.json")
SECRET_KEY = "wswhisper2026_super_key"

def _xor_crypt(string, key):
    return "".join(chr(ord(c) ^ ord(key[i % len(key)])) for i, c in enumerate(string))

def encrypt_key(password):
    if not password: return ""
    try:
        xored = _xor_crypt(password, SECRET_KEY)
        return base64.b64encode(xored.encode('utf-8')).decode('utf-8')
    except Exception:
        return ""

def decrypt_key(token):
    if not token: return ""
    try:
        xored = base64.b64decode(token.encode('utf-8')).decode('utf-8')
        return _xor_crypt(xored, SECRET_KEY)
    except Exception:
        return token # Если вдруг это старый ключ без шифрования

def load_config():
    default_config = {
        "engine": "Whisper (Offline)",
        "groq_api_key": "",
        "language": "ru",
        "hotkey": "ctrl+alt"
    }

    if not os.path.exists(CONFIG_FILE):
        save_config(default_config)
        return default_config

    try:
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            config = json.load(f)
            # Дозаполняем отсутствующие ключи
            for key, value in default_config.items():
                if key not in config:
                    config[key] = value
            return config
    except Exception as e:
        print(f"Ошибка чтения конфига: {e}")
        return default_config

def save_config(config):
    try:
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=4, ensure_ascii=False)
    except Exception as e:
        print(f"Ошибка сохранения конфига: {e}")
