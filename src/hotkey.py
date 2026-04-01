import keyboard
import time
import threading

class HotkeyManager:
    def __init__(self, initial_hotkey='ctrl+alt', on_start=None, on_stop=None):
        self.hotkey = initial_hotkey
        self.on_start = on_start
        self.on_stop = on_stop
        self.is_pressed = False
        self.is_active = True  # Контролируется переключателем из GUI
        self._listener_thread = None
        self._stop_event = threading.Event()

    def set_hotkey(self, new_hotkey):
        self.hotkey = str(new_hotkey).strip()
        self.is_pressed = False

    def disable(self):
        self.is_active = False
        
    def enable(self):
        self.is_active = True

    def start_listening_bg(self):
        """Запускает прослушку на фоне, чтобы не вешать GUI"""
        if self._listener_thread is None or not self._listener_thread.is_alive():
            self._stop_event.clear()
            self._listener_thread = threading.Thread(target=self._listen, daemon=True)
            self._listener_thread.start()

    def stop_listening_bg(self):
        self._stop_event.set()

    def _listen(self):
        print(">> Перехватчик горячих клавиш запущен на фоне.")
        while not self._stop_event.is_set():
            if not self.is_active or not self.hotkey:
                time.sleep(0.1)
                continue

            try:
                pressed = keyboard.is_pressed(self.hotkey)
            except ValueError:
                # Если введена кривая строка хоткея — считаем не нажатым
                pressed = False
                
            if pressed:
                if not self.is_pressed:
                    self.is_pressed = True
                    if self.on_start:
                        self.on_start()
            else:
                if self.is_pressed:
                    self.is_pressed = False
                    if self.on_stop:
                        self.on_stop()
            time.sleep(0.05)
        print(">> Перехватчик остановлен.")
