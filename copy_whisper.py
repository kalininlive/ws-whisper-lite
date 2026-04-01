import os
import shutil
import urllib.request
import sys
import zipfile
import tempfile

dest_dir = r"C:\DictationApp\bin"
models_dir = r"C:\DictationApp\models"

os.makedirs(dest_dir, exist_ok=True)
os.makedirs(models_dir, exist_ok=True)

def reporthook(blocknum, blocksize, totalsize):
    readsofar = blocknum * blocksize
    if totalsize > 0:
        percent = readsofar * 100.0 / totalsize
        sys.stdout.write(f"\r[{percent:5.1f}%] Загружено {readsofar / (1024*1024):.2f} MB")
        sys.stdout.flush()

print("--- 1. Загрузка и установка бинарников Whisper ---")
WHISPER_ZIP_URL = "https://github.com/ggerganov/whisper.cpp/releases/latest/download/whisper-bin-Win32.zip"

files_to_copy = [
    "whisper-cli.exe",
    "ggml.dll",
    "ggml-cpu.dll",
    "ggml-base.dll",
    "whisper.dll",
    "SDL2.dll"
]

missing_binaries = any(not os.path.exists(os.path.join(dest_dir, f)) for f in files_to_copy)

if missing_binaries:
    print(f"Скачиваем 32-битную версию Whisper (Win32) (около 4 МБ) по ссылке:\n{WHISPER_ZIP_URL}")
    with tempfile.TemporaryDirectory() as tmpdirname:
        zip_path = os.path.join(tmpdirname, "whisper.zip")
        try:
            urllib.request.urlretrieve(WHISPER_ZIP_URL, zip_path, reporthook)
            print("\nУспешно скачан архив. Извлекаем файлы...")
            with zipfile.ZipFile(zip_path, 'r') as zf:
                for zinfo in zf.infolist():
                    filename = os.path.basename(zinfo.filename)
                    if filename in files_to_copy:
                        with zf.open(zinfo.filename) as source, open(os.path.join(dest_dir, filename), "wb") as target:
                            shutil.copyfileobj(source, target)
                        print(f"-> Извлечен и установлен {filename}")
        except Exception as e:
            print(f"\nОшибка скачивания бинарников: {e}")
            print(f"Пожалуйста, скачайте архив вручную: {WHISPER_ZIP_URL}")
            print(f"И распакуйте нужные файлы: {', '.join(files_to_copy)} в папку {dest_dir}")
else:
    print("Бинарники Whisper уже установлены. Пропускаем.")

print("\n--- 2. Загрузка языковой модели ---")
MODEL_URL = "https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-base.bin"
model_path = os.path.join(models_dir, "ggml-base.bin")

if not os.path.exists(model_path):
    print(f"Скачиваем ggml-base.bin (около 142 МБ) в {model_path}...")
    try:
        urllib.request.urlretrieve(MODEL_URL, model_path, reporthook)
        print("\nУспешно скачана модель!")
    except Exception as e:
        print(f"\nОшибка скачивания модели: {e}")
        print("Пожалуйста, скачайте модель вручную по ссылке:")
        print(MODEL_URL)
        print(f"И положите её в {model_path}")
else:
    print("Модель ggml-base.bin уже существует. Пропускаем.")

print("\nВсе нужные файлы установлены! Можно запускать src/main.py")
