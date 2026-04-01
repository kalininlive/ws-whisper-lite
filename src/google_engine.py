import numpy as np
import speech_recognition as sr

class GoogleEngine:
    def __init__(self):
        self.recognizer = sr.Recognizer()
        print("Инициализация движка Google...")
        
    def transcribe(self, audio_data, language="ru-RU"):
        if len(audio_data) == 0:
            return ""
            
        print("Распознавание через Google...")
        
        audio_int16 = np.int16(audio_data * 32767)
        raw_audio_bytes = audio_int16.tobytes()
        
        audio_src = sr.AudioData(raw_audio_bytes, 16000, 2)
        
        try:
            text = self.recognizer.recognize_google(audio_src, language=language)
            return text
        except sr.UnknownValueError:
            # Если Google услышал тишину или шум и не смог извлечь текст
            print(">>>> Тишина (или неразборчивая речь).")
            return ""
        except sr.RequestError as e:
            print(f"\n[ОШИБКА ИНТЕРНЕТА] Ошибка соединения с серверами Google: {e}\n")
            return ""
        except Exception as e:
            print(f"\n[СИСТЕМНАЯ ОШИБКА] {e}\n")
            return ""
