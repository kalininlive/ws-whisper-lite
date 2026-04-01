import os
import sys
import threading
import logging
import traceback

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Устанавливаем запись всех логов и ошибок в файл c:\DictationApp\log.txt
log_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "log.txt")
logging.basicConfig(filename=log_file, level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    encoding='utf-8')

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
from config import load_config, save_config, decrypt_key, CONFIG_PATH
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
        self.google_engine = GoogleEngine()
        self.groq_engine = None 
        
        # Переменные для стриминга (нарезания аудио частями)
        self.last_processed_sample = 0
        self.is_processing = False # Флаг, чтобы не запускать обработку, если предыдущий чанк еще не готов
        self.is_recording = False  # Флаг текущей записи
        
        # ЛАЙТ-ВЕРСИЯ: Офлайн Whisper больше не требуется.
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
        
        # Безопасный инжект функции для чтения громкости из UI потока
        self.gui.visualizer.set_volume_getter(lambda: self.recorder.current_volume)

    def handle_config_save(self, new_config):
        self.config = new_config
        save_config(self.config)
        self.hk_manager.set_hotkey(self.config.get("hotkey"))
        # Применяем настройки автозагрузки
        set_autostart(self.config.get("autostart", False))

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
        self.last_processed_sample = 0
        self.is_processing = False
        self.is_recording = True
        self.recorder.start()
        
        # Запускаем цикл стриминга через 3 секунды
        QTimer.singleShot(3000, self._check_streaming_chunk)

    def on_mic_stop(self):
        self.is_recording = False
        
        # QTimer.singleShot гарантирует вызов метода в UI потоке
        QTimer.singleShot(0, lambda: self.gui.visualizer.set_volume(0.0))
        logging.info("Горячая клавиша отпущена. Остановка записи...")
        self.set_gui_status("Распознавание финала...")
        
        try:
            # Получаем остаток аудио (от последней отметки до конца)
            audio_data = self.recorder.stop()
            final_chunk = audio_data[self.last_processed_sample:]
            
            if len(final_chunk) > 0:
                threading.Thread(target=self._process_audio, args=(final_chunk, True), daemon=True).start()
            else:
                self.set_gui_status("Готово")
        except Exception as e:
            logging.error(f"Ошибка при остановке аудио: {e}", exc_info=True)
            self.set_gui_status(f"ОШИБКА: {str(e)}")

    def _check_streaming_chunk(self):
        # Логика стриминга (упрощена для примера)
        pass

    def _process_audio(self, audio_data, is_final=False):
        try:
            if not is_final:
                self.set_gui_status("Распознаю часть...")
            
            # Определение языка: если Auto - берем язык системы
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

            # Предподготовка для разных движков
            engine_type = self.config.get("engine", "Groq")
            
            # Генерируем специфичный код для Google (ISO-639-1 + ISO-3166-1)
            google_lang = "ru-RU" if lang == "ru" else f"{lang}-{lang.upper()}"
            if lang == "en": google_lang = "en-US"
            
            # Для Groq оставляем 2 буквы
            groq_lang = lang
            
            text = ""
            if engine_type == "Groq":
                key_encrypted = self.config.get("groq_api_key", "").strip()
                if not key_encrypted:
                    self.set_gui_status("ОШИБКА: Задайте API-Ключ в настройках!")
                    self.is_processing = False
                    return
                
                real_key = decrypt_key(key_encrypted)
                
                if not self.groq_engine or getattr(self.groq_engine, "api_key", None) != real_key:
                    from groq_engine import GroqEngine
                    self.groq_engine = GroqEngine(api_key=real_key)
                    
                text = self.groq_engine.transcribe(audio_data, language=groq_lang)
            else:
                text = self.google_engine.transcribe(audio_data, language=google_lang)

            if text:
                logging.info(f"Распознано ({engine_type}): '{text}'")
                self.set_gui_status(f"Вставлено: '{text[:20]}...'")
                from injector import paste_text
                paste_text(text)
            else:
                logging.info(f"Сервис ({engine_type}) вернул пустую строку.")
                self.set_gui_status("Тишина или нераспознано")
        except Exception as e:
            self.set_gui_status(f"ОШИБКА: {str(e)}")

    def run(self):
        self.hk_manager.start_listening_bg()
        self.gui.show()
        sys.exit(self.qapp.exec())

    def shutdown(self):
        self.hk_manager.stop_listening_bg()

if __name__ == "__main__":
    app = Application()
    app.run()
