import ctypes
import time
import pyperclip
import win32clipboard

# Структуры Windows C-API для SendInput
PUL = ctypes.POINTER(ctypes.c_ulong)

class KeyBdInput(ctypes.Structure):
    _fields_ = [("wVk", ctypes.c_ushort),
                ("wScan", ctypes.c_ushort),
                ("dwFlags", ctypes.c_ulong),
                ("time", ctypes.c_ulong),
                ("dwExtraInfo", PUL)]

class HardwareInput(ctypes.Structure):
    _fields_ = [("uMsg", ctypes.c_ulong),
                ("wParamL", ctypes.c_short),
                ("wParamH", ctypes.c_ushort)]

class MouseInput(ctypes.Structure):
    _fields_ = [("dx", ctypes.c_long),
                ("dy", ctypes.c_long),
                ("mouseData", ctypes.c_ulong),
                ("dwFlags", ctypes.c_ulong),
                ("time", ctypes.c_ulong),
                ("dwExtraInfo", PUL)]

class Input_I(ctypes.Union):
    _fields_ = [("ki", KeyBdInput),
                ("mi", MouseInput),
                ("hi", HardwareInput)]

class Input(ctypes.Structure):
    _fields_ = [("type", ctypes.c_ulong),
                ("ii", Input_I)]

# Константы VK (Virtual Keys)
VK_CONTROL = 0x11
VK_V = 0x56

# Флаги
KEYEVENTF_KEYUP = 0x0002
INPUT_KEYBOARD = 1

def send_key(vk_code, key_up=False):
    extra = ctypes.c_ulong(0)
    ii_ = Input_I()
    flags = KEYEVENTF_KEYUP if key_up else 0
    ii_.ki = KeyBdInput(vk_code, 0, flags, 0, ctypes.pointer(extra))
    x = Input(ctypes.c_ulong(INPUT_KEYBOARD), ii_)
    ctypes.windll.user32.SendInput(1, ctypes.pointer(x), ctypes.sizeof(x))

def paste_text(text):
    if not text:
        return

    # 1. Запоминаем текущий буфер обмена (текст)
    old_clipboard = ""
    try:
        old_clipboard = pyperclip.paste()
    except Exception:
        pass

    # 2. Помещаем распознанный текст в буфер
    pyperclip.copy(text)

    # 3. Эмулируем аппаратные нажатия Ctrl+V
    time.sleep(0.05)              # Дадим Windows время осознать копирование
    send_key(VK_CONTROL, False)   # Ctrl Down
    time.sleep(0.02)
    send_key(VK_V, False)         # V Down
    time.sleep(0.03)
    send_key(VK_V, True)          # V Up
    time.sleep(0.02)
    send_key(VK_CONTROL, True)    # Ctrl Up

    # 4. ВАЖНО: Асинхронная пауза. Ждем, пока целевое окно не прочитает буфер обмена!
    # Увеличено до 0.5с для надежности на медленных ПК
    time.sleep(0.5)

    # 5. Восстанавливаем оригинальные данные пользователя
    if old_clipboard:
        try:
            pyperclip.copy(old_clipboard)
        except Exception:
            pass
    else:
        # Если буфер был чист
        try:
            win32clipboard.OpenClipboard()
            win32clipboard.EmptyClipboard()
            win32clipboard.CloseClipboard()
        except Exception:
            pass
