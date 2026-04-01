import os
import subprocess
import wave
import numpy as np
import tempfile

class WhisperEngine:
    def __init__(self, model_path, cli_path):
        self.model_path = model_path
        self.cli_path = cli_path
        
        print(f"Инициализация движка {os.path.basename(self.cli_path)} с моделью {os.path.basename(self.model_path)}...")
        
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Модель не найдена: {model_path}")
        if not os.path.exists(cli_path):
            raise FileNotFoundError(f"Исполняемый файл whisper не найден: {cli_path}")

    def _save_wav(self, audio_data, path):
        # Конвертация float32 (-1.0 ... 1.0) в int16
        audio_int16 = np.int16(audio_data * 32767)
        with wave.open(path, 'wb') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2) # 2 bytes
            wf.setframerate(16000)
            wf.writeframes(audio_int16.tobytes())

    def transcribe(self, audio_data):
        if len(audio_data) == 0:
            return ""
        
        # Сохраняем во временный файл
        tmp_wav = os.path.join(tempfile.gettempdir(), "dictation_tmp.wav")
        self._save_wav(audio_data, tmp_wav)
        
        print(f"Распознавание...")
        
        # Запуск whisper.cpp. Флаг -nt убирает таймстампы, -l ru задает язык
        cmd = [
            self.cli_path,
            "-m", self.model_path,
            "-f", tmp_wav,
            "-nt", 
            "-l", "ru"
        ]
        
        # Запускаем скрытое консольное окно, чтобы не мелькало
        creationflags = 0
        if os.name == 'nt':
            creationflags = subprocess.CREATE_NO_WINDOW
            
        result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', creationflags=creationflags)
        
        if result.returncode != 0:
            print(f"\n[ОШИБКА WHISPER] Код: {result.returncode}\nВывод: {result.stderr}\n")
            
        # Очищаем текст от лишних пробельных символов
        text = result.stdout.strip()
        
        # Удаляем временный файл
        try:
            os.remove(tmp_wav)
        except Exception:
            pass
            
        return text
