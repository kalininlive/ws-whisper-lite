import os
import sys
import threading
import logging
import traceback
import time
import numpy as np
import winreg

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Устанавливаем запись всех логов и ошибок в файл c:\DictationApp\log.txt и в консоль
log_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "log.txt")
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    encoding='utf-8',
                    handlers=[
                        logging.FileHandler(log_file, encoding='utf-8'),
                        logging.StreamHandler(sys.stdout)
                    ])

# Перехватчик всех неперехваченных исключений
def log_uncaught_exceptions(ex_cls, ex, tb):
    logging.critical("Неперехваченная ошибка:", exc_info=(ex_cls, ex, tb))
sys.excepthook = log_uncaught_exceptions

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer
from audio import AudioRecorder
from hotkey import HotkeyManager
from google_engine import GoogleEngine
from groq_engine import GroqEngine
from injector import paste_text
from config import load_config, save_config, decrypt_key, CONFIG_FILE
from gui import FuturisticWidget

def set_autostart(enabled):
    """Добавляет или удаляет программу из автозагрузки через реестр."""
    key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
    app_name = "WSWhisper"
    # В режиме сборки Nuitka --onefile sys.argv[0] указывает на EXE
    app_path = os.path.abspath(sys.argv[0])
    
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE)
        if enabled:
            winreg.SetValueEx(key, app_name, 0, winreg.REG_SZ, f'"{app_path}"')
        else:
            try:
                winreg.DeleteValue(key, app_name)
            except FileNotFoundError:
                pass
        winreg.CloseKey(key)
        logging.info(f"Autostart {'enabled' if enabled else 'disabled'}")
        return True
    except Exception as e:
        logging.error(f"Failed to set autostart: {e}")
        return False

class Application:
    def __init__(self):
        self.qapp = QApplication(sys.argv)
        
        self.config = load_config()
        self.google_engine = GoogleEngine(proxy_config=self.config)
        groq_key = self.config.get("groq_api_key", "")
        self.groq_engine = GroqEngine(api_key=decrypt_key(groq_key), proxy_config=self.config) if groq_key else None
        
        # Состояние приложения
        self.is_recording = False  
        
        logging.info("Инициализация в режиме Cloud-only (Google & Groq).")

        self.recorder = AudioRecorder(sample_rate=16000, channels=1)
        
        self.gui = FuturisticWidget(
            config=self.config,
            on_config_save=self.handle_config_save,
            on_toggle=self.handle_toggle,
            on_quit=self.shutdown
        )
        
        self.hk_manager = HotkeyManager(
            initial_hotkey=self.config.get("hotkey", "ctrl+alt"),
            on_start=self.on_mic_start,
            on_stop=self.on_mic_stop
        )
        
        # --- ПРОВЕРКА СВЯЗИ ПРИ СТАРТЕ ---
        QTimer.singleShot(1000, self._perform_startup_check)
        
        # Безопасный инжект функции для чтения громкости из UI потока
        self.gui.visualizer.set_volume_getter(lambda: self.recorder.current_volume)

    def handle_config_save(self, new_config):
        """Обработка сохранения настроек."""
        save_config(new_config)
        self.config = new_config
        self.hk_manager.set_hotkey(self.config.get("hotkey"))
        # Применяем настройки автозагрузки
        set_autostart(self.config.get("autostart", False))
        
        # Переинициализируем движки с новыми ключами/прокси
        self.google_engine = GoogleEngine(proxy_config=self.config)
        
        groq_key = self.config.get("groq_api_key", "")
        if groq_key:
            self.groq_engine = GroqEngine(api_key=decrypt_key(groq_key), proxy_config=self.config)
        else:
            self.groq_engine = None
        
        logging.info("[CONFIG] Настройки обновлены (в т.ч. Прокси).")
        self.gui.set_status("Настройки сохранены")

    def handle_toggle(self, is_active):
        if is_active:
            self.hk_manager.enable()
        else:
            self.hk_manager.disable()

    def set_gui_status(self, msg):
        # Обертка для безопасного обновления UI из других потоков
        QTimer.singleShot(0, lambda: self.gui.set_status(msg))

    def on_mic_start(self):
        logging.info("Горячая клавиша нажата. Запуск записи...")
        self.set_gui_status("[REC] Запись начата...")
        self.is_recording = True
        self.recorder.start()

    def on_mic_stop(self):
        self.is_recording = False
        
        # QTimer.singleShot гарантирует вызов метода в UI потоке
        QTimer.singleShot(0, lambda: self.gui.visualizer.set_volume(0.0))
        logging.info("Горячая клавиша отпущена. Остановка записи...")
        try:
            # Получаем полное аудио за один раз
            audio_data = self.recorder.stop()
            
            if len(audio_data) > 0:
                self.set_gui_status("Распознавание...")
                threading.Thread(target=self._process_audio, args=(audio_data, True), daemon=True).start()
            else:
                self.set_gui_status("Готово")
        except Exception as e:
            logging.error(f"Ошибка при остановке аудио: {e}", exc_info=True)
            self.set_gui_status(f"ОШИБКА: {str(e)}")

    def _process_audio(self, audio_data, is_final=True):
        try:
            logging.info(f"[MAIN] Начало обработки аудио (размер: {len(audio_data)} семплов)...")
            
            # Определение языка
            lang = self.config.get("language", "Auto")
            if lang == "Auto":
                try:
                    import locale
                    def_lang = locale.getdefaultlocale()[0]
                    if def_lang:
                        lang = def_lang.split('_')[0].lower()
                    else:
                        lang = "ru"
                except:
                    lang = "ru"

            engine_type = self.config.get("engine", "Groq")
            google_lang = "ru-RU" if lang == "ru" else f"{lang}-{lang.upper()}"
            if lang == "en": google_lang = "en-US"
            groq_lang = lang
            
            logging.info(f"[MAIN] Используется движок: {engine_type} (Язык: {lang})")
            
            text = ""
            if engine_type == "Groq":
                if not self.groq_engine:
                    self.set_gui_status("ОШИБКА: Задайте API-Ключ!")
                    return
                logging.info("[MAIN] Отправка данных в Groq (Whisper V3)...")
                text = self.groq_engine.transcribe(audio_data, language=groq_lang)
            else:
                logging.info("[MAIN] Отправка данных в Google Speech API...")
                text = self.google_engine.transcribe(audio_data, language=google_lang)

            if text.startswith("ERROR:"):
                logging.error(f"[MAIN] Сервис {engine_type} вернул ошибку: {text}")
                msg = "Сервис заблокирован. Включите Телепорт или установите Прокси в настройках"
                if "NETWORK" in text or "GEOBLOCK" in text or "UNKNOWN" in text:
                    self.gui.show_alert(msg)
                    self.set_gui_status("ОШИБКА ДИКТОВКИ (Нужен Телепорт)")
                else:
                    self.set_gui_status(f"ОШИБКА: {text.split(':')[-1]}")
            elif text:
                logging.info(f"Распознано ({engine_type}): '{text}'")
                self.set_gui_status(f"Вставлено: '{text[:20]}...'")
                
                from injector import paste_text
                # Добавляем пробел в конце, чтобы следующая диктовка не слипалась
                paste_text(text + " ")
            else:
                logging.info(f"Сервис ({engine_type}) вернул пустую строку.")
                self.set_gui_status("Тишина...")
        except Exception as e:
            self.set_gui_status(f"ОШИБКА: {str(e)}")

    def run(self):
        self.hk_manager.start_listening_bg()
        self.gui.show()
        sys.exit(self.qapp.exec())

    def shutdown(self):
        self.hk_manager.stop_listening_bg()

    def _perform_startup_check(self):
        """Проверка доступности сервисов при запуске."""
        def check():
            logging.info("[CHECK] Запуск стартовой диагностики сети...")
            
            # Проверка Google (всегда есть)
            google_status = self.google_engine.check_connectivity()
            
            # Проверка Groq (только если есть ключ)
            groq_status = True
            if self.groq_engine:
                groq_status = self.groq_engine.check_connectivity()
            
            # Если хотя бы один сервис выдает GEOBLOCK или NETWORK ERROR
            is_blocked = any(s in [google_status, groq_status] for s in ["ERROR:NETWORK", "ERROR:GEOBLOCK", "ERROR:403", "ERROR:403"])
            
            if is_blocked:
                logging.warning(f"[CHECK] Обнаружена блокировка (Google:{google_status}, Groq:{groq_status}).")
                # Всегда предлагаем Телепорт/Прокси, если что-то не так
                self.gui.show_alert("Сервис заблокирован. Включите Телепорт или установите Прокси в настройках")
            else:
                logging.info("[CHECK] Сеть в порядке.")

        threading.Thread(target=check, daemon=True).start()

if __name__ == "__main__":
    app = Application()
    app.run()
