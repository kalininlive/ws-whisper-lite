import os
import time
import httpx
from groq import Groq
import wave
import numpy as np
import logging

class GroqEngine:
    def __init__(self, api_key, proxy_config=None):
        self.api_key = api_key
        try:
            proxies = None
            if proxy_config and proxy_config.get("proxy_enabled"):
                p_host = proxy_config.get("proxy_ip")
                p_port = proxy_config.get("proxy_port")
                p_user = proxy_config.get("proxy_user")
                p_pass = proxy_config.get("proxy_pass")
                
                if p_host and p_port:
                    if p_user and p_pass:
                        proxy_url = f"http://{p_user}:{p_pass}@{p_host}:{p_port}"
                    else:
                        proxy_url = f"http://{p_host}:{p_port}"
                    proxies = {"http://": proxy_url, "https://": proxy_url}
                    logging.info(f"[GROQ] Использование прокси: {p_host}:{p_port}")

            self.proxies = proxies
            http_client = httpx.Client(proxies=proxies) if proxies else None
            self.client = Groq(api_key=api_key, http_client=http_client)
            
            logging.info("Инициализация облачного движка Groq (Whisper Large v3)...")
        except Exception as e:
            logging.error(f"[GROQ] Ошибка инициализации: {e}")
            self.client = None

    def check_connectivity(self):
        """Проверка связи с Groq через httpx."""
        try:
            with httpx.Client(timeout=5.0, proxies=self.proxies) as client:
                res = client.get("https://api.groq.com/openai/v1/models")
                if res.status_code in [200, 401]: # 401 is OK for connectivity
                    return True
                if res.status_code == 403:
                    return "ERROR:GEOBLOCK"
                return f"ERROR:{res.status_code}"
        except Exception as e:
            logging.error(f"[GROQ] Ошибка проверки: {e}")
            return "ERROR:NETWORK"

    def transcribe(self, audio_data, language="ru"):
        if not self.client:
            return "ERROR:NOT_INIT"
        if len(audio_data) == 0:
            logging.warning("[GROQ] Пустое аудио, отмена.")
            return ""
            
        logging.info(f"[GROQ] Начало распознавания (Язык: {language}, семплов: {len(audio_data)})...")
        
        # Конвертация float32 (-1.0 ... 1.0) в int16
        import numpy as np
        audio_int16 = np.int16(audio_data * 32767)
        temp_wav = os.path.join(os.environ.get("TEMP", "."), f"temp_groq_{int(time.time())}.wav")
        
        try:
            import wave
            with wave.open(temp_wav, "wb") as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(16000)
                wf.writeframes(audio_int16.tobytes())
            
            logging.info(f"[GROQ] Аудио сохранено во временный файл: {temp_wav}")
            
            # API Groq
            with open(temp_wav, "rb") as file:
                logging.info("[GROQ] Отправка запроса в API Groq...")
                translation = self.client.audio.transcriptions.create(
                    file=(temp_wav, file.read()),
                    model="whisper-large-v3",
                    language=language[:2].lower() if language else "ru",
                    response_format="json"
                )
            
            text = translation.text
            logging.info(f"[GROQ] Успех! Получено {len(text)} символов.")
            return text
            
        except Exception as e:
            err_msg = str(e).lower()
            logging.error(f"[GROQ] Ошибка API: {e}")
            
            if "forbidden" in err_msg or "403" in err_msg:
                return "ERROR:GEOBLOCK"
            if "unauthorized" in err_msg or "401" in err_msg:
                return "ERROR:AUTH"
            if "rate limit" in err_msg or "429" in err_msg:
                return "ERROR:RATELIMIT"
            if "connect" in err_msg or "timeout" in err_msg or "network" in err_msg:
                return "ERROR:NETWORK"
            return f"ERROR:{str(e)}"
            
        finally:
            if os.path.exists(temp_wav):
                try: os.remove(temp_wav)
                except: pass
