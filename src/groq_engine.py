import os
from groq import Groq
from io import BytesIO
import wave
import numpy as np

class GroqEngine:
    def __init__(self, api_key):
        self.api_key = api_key
        try:
            self.client = Groq(api_key=api_key)
            print("Инициализация облачного движка Groq (Whisper Large v3)...")
        except Exception as e:
            print(f"[ERROR] Не удалось инициализировать Groq: {e}")
            self.client = None

    def transcribe(self, audio_data, language="ru"):
        if not self.client:
            print("[ERROR] Groq API клиент не инициализирован (проверьте настройки ключа).")
            return ""
        if len(audio_data) == 0:
            return ""

        print(f"Распознавание через Groq (Язык: {language})...")

        # Конвертация float32 (-1.0 ... 1.0) в int16
        audio_int16 = np.int16(audio_data * 32767)

        # Groq ожидает файловый объект (WAV). Эмулируем его в оперативной памяти!
        wav_io = BytesIO()
        with wave.open(wav_io, 'wb') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(16000)
            wf.writeframes(audio_int16.tobytes())
        
        # Сброс указателя на начало, чтобы API прочитало байты
        wav_io.seek(0)
        # Groq endpoint строго требует у объекта имя с расширением (например, audio.wav)
        wav_io.name = "audio.wav" 

        try:
            kwargs = {
                "file": (wav_io.name, wav_io.read()),
                "model": "whisper-large-v3",
                "response_format": "text"
            }
            if language and isinstance(language, str) and len(language) >= 2:
                # Groq strictly expects ISO-639-1 two-letter code
                kwargs["language"] = language[:2].lower()

            # Отправка аудио на сервера сверхбыстрого вывода LPU
            translation = self.client.audio.transcriptions.create(**kwargs)
            return translation.strip() if hasattr(translation, "strip") else str(translation).strip()
        except Exception as e:
            import logging
            logging.error(f"[ОШИБКА GROQ] Вызов не прошел: {e}", exc_info=True)
            print(f"\n[ОШИБКА GROQ] Вызов не прошел. Возможно, неверный ключ? Ошибка: {e}\n")
            return ""
