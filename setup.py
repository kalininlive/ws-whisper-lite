import os
import sys
import urllib.request
import zipfile
import subprocess

ROOT = os.path.dirname(os.path.abspath(__file__))
BIN_DIR = os.path.join(ROOT, "bin")
MODELS_DIR = os.path.join(ROOT, "models")

# Ссылки на официальные релизы
WHISPER_URL = "https://github.com/ggerganov/whisper.cpp/releases/download/v1.6.2/whisper-bin-x64.zip"
MODEL_URL = "https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-small.bin"

def reporthook(blocknum, blocksize, totalsize):
    readsofar = blocknum * blocksize
    if totalsize > 0:
        percent = readsofar * 100.0 / totalsize
        sys.stdout.write(f"\r[{percent:5.1f}%] Загружено {readsofar / (1024*1024):.2f} MB из {totalsize / (1024*1024):.2f} MB")
        sys.stdout.flush()
        if readsofar >= totalsize:
            sys.stdout.write("\n")

def download_file(url, dest):
    print(f"Скачивание {os.path.basename(dest)}...")
    urllib.request.urlretrieve(url, dest, reporthook)

def main():
    os.makedirs(BIN_DIR, exist_ok=True)
    os.makedirs(MODELS_DIR, exist_ok=True)

    print("--- ШАГ 1: Установка Python зависимостей ---")
    req_path = os.path.join(ROOT, 'requirements.txt')
    subprocess.run([sys.executable, "-m", "pip", "install", "-r", req_path], check=True)

    print("\n--- ШАГ 2: Загрузка Windows-бинарника whisper.cpp ---")
    zip_path = os.path.join(BIN_DIR, "whisper.zip")
    if not os.path.exists(os.path.join(BIN_DIR, "whisper-cli.exe")):
        download_file(WHISPER_URL, zip_path)
        print("Распаковка архива...")
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(BIN_DIR)
        
        # Переименовываем main.exe в whisper-cli.exe (как мы указали в коде)
        main_exe = os.path.join(BIN_DIR, "main.exe")
        target_exe = os.path.join(BIN_DIR, "whisper-cli.exe")
        if os.path.exists(main_exe):
            os.rename(main_exe, target_exe)
            
        try:
            os.remove(zip_path)
        except Exception:
            pass
    else:
        print("Бинарник whisper-cli.exe уже найден.")

    print("\n--- ШАГ 3: Загрузка языковой модели ggml-small.bin ---")
    model_path = os.path.join(MODELS_DIR, "ggml-small.bin")
    if not os.path.exists(model_path):
        download_file(MODEL_URL, model_path)
    else:
        print("Модель уже найдена.")

    print("\n=============================================")
    print("Установка успешна! Все файлы на своих местах.")
    print("=============================================")

if __name__ == "__main__":
    main()
