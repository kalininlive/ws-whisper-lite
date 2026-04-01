import numpy as np
import speech_recognition as sr
import logging

class GoogleEngine:
    def __init__(self, proxy_config=None):
        self.recognizer = sr.Recognizer()
        self.proxy_config = proxy_config
        logging.info("Инициализация движка Google (SpeechRecognition)...")
        
    def _get_proxy_url(self):
        """Формирует URL прокси для Google."""
        if not self.proxy_config or not self.proxy_config.get("proxy_enabled"):
            return None
            
        p_host = self.proxy_config.get("proxy_ip")
        p_port = self.proxy_config.get("proxy_port")
        p_user = self.proxy_config.get("proxy_user")
        p_pass = self.proxy_config.get("proxy_pass")
        
        if not p_host or not p_port:
            return None
            
        if p_user and p_pass:
            return f"http://{p_user}:{p_pass}@{p_host}:{p_port}"
        return f"http://{p_host}:{p_port}"
        
    def check_connectivity(self):
        """Быстрая проверка доступности серверов Google без аудио."""
        import http.client
        try:
            proxy_url = self._get_proxy_url()
            if proxy_url:
                # Parsing proxy for http.client
                from urllib.parse import urlparse
                p = urlparse(proxy_url)
                conn = http.client.HTTPSConnection(p.hostname, p.port, timeout=3)
                if p.username and p.password:
                    import base64
                    auth = base64.b64encode(f"{p.username}:{p.password}".encode()).decode()
                    conn.set_tunnel("www.google.com", headers={"Proxy-Authorization": f"Basic {auth}"})
                else:
                    conn.set_tunnel("www.google.com")
            else:
                conn = http.client.HTTPSConnection("www.google.com", timeout=3)
                
            conn.request("HEAD", "/")
            res = conn.getresponse()
            conn.close()
            if res.status == 200:
                return True
            return f"ERROR:{res.status}"
        except Exception:
            return "ERROR:NETWORK"

    def transcribe(self, audio_data, language="ru-RU"):
        if len(audio_data) == 0:
            logging.warning("[GOOGLE] Пустое аудио, отмена.")
            return ""
            
        logging.info(f"[GOOGLE] Начало распознавания (Язык: {language}, семплов: {len(audio_data)})...")
        
        audio_int16 = np.int16(audio_data * 32767)
        raw_audio_bytes = audio_int16.tobytes()
        
        audio_src = sr.AudioData(raw_audio_bytes, 16000, 2)
        
        try:
            logging.info("[GOOGLE] Отправка запроса на сервера Google Speech API...")
            proxy_url = self._get_proxy_url()
            
            # Use environment variables for proxy as recognize_google uses urllib
            import os
            old_http = os.environ.get("http_proxy")
            old_https = os.environ.get("https_proxy")
            
            if proxy_url:
                os.environ["http_proxy"] = proxy_url
                os.environ["https_proxy"] = proxy_url
            
            try:
                text = self.recognizer.recognize_google(audio_src, language=language)
            finally:
                # Restore original env
                if old_http: os.environ["http_proxy"] = old_http
                elif "http_proxy" in os.environ: del os.environ["http_proxy"]
                
                if old_https: os.environ["https_proxy"] = old_https
                elif "https_proxy" in os.environ: del os.environ["https_proxy"]

            logging.info(f"[GOOGLE] Успех! Получено '{text[:20]}...'")
            return text
        except sr.UnknownValueError:
            logging.warning("[GOOGLE] Речь не распознана.")
            return ""
        except sr.RequestError as e:
            logging.error(f"[GOOGLE] Ошибка запроса: {e}")
            return "ERROR:NETWORK"
        except Exception as e:
            logging.error(f"[GOOGLE] Непредвиденная ошибка: {e}")
            return f"ERROR:{str(e)}"
