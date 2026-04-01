import sys
import threading
import os
import math
import time
import locale

from PySide6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                               QLabel, QDialog, QComboBox, QLineEdit, QSystemTrayIcon, QMenu,
                               QGraphicsDropShadowEffect, QFrame, QSpacerItem, QSizePolicy)
from PySide6.QtCore import Qt, QPropertyAnimation, QRect, QRectF, QTimer, QSize, QEasingCurve, QCoreApplication, Property
from PySide6.QtGui import QIcon, QColor, QFont, QPixmap, QPainter, QBrush, QCursor, QKeyEvent, QPainterPath, QLinearGradient, QRadialGradient, QPen
from config import encrypt_key, decrypt_key
import webbrowser

LOGO_PATH = r"C:\Users\kalib\.gemini\antigravity\brain\868b2227-c940-40f6-952e-edfce0c75007\wswhisper_logo_1775022979626.png"

# ================= LOCALIZATION =================
lang_code = locale.getdefaultlocale()[0]
is_ru = lang_code and lang_code.startswith("ru")

if is_ru:
    T_STATUS_ACTIVE = "Статус: Активен"
    T_STATUS_OFFLINE = "Статус: Остановлен"
    T_STATUS_REC = "Статус: Запись..."
    T_STATUS_PROC = "Статус: Обработка"
    T_STATUS_ERR = "Статус: ОШИБКА"
    T_READY = "Горячие клавиши включены"
    T_STANDBY = "Ожидание системы"
    T_LISTENING = "Слушаю аудиопоток..."
    
    L_SETTINGS_TITLE = "НАСТРОЙКИ"
    L_ENGINE = "ПРОВАЙДЕР РАСПОЗНАВАНИЯ"
    L_LANG = "ЯЗЫК ДИКТОВКИ"
    L_HOTKEY = "ГОРЯЧИЕ КЛАВИШИ"
    L_SAVE = "СОХРАНИТЬ ИЗМЕНЕНИЯ"
    L_BTN_SETT = "⚙ НАСТРОЙКИ"
    
    LINKS_TEXT = (
        "<a href='https://t.me/websansay' style='color:#00ffa3; text-decoration:none;'>ℹ Разработчик @websansay</a><br><br>"
        "<a href='https://t.me/+FB4-Dd_lelJkNjJi' style='color:#00ffa3; text-decoration:none;'>📣 TG Channel WS</a><br><br>"
        "<a href='https://boosty.to/websansay/donate' style='color:#00eeff; text-decoration:none;'>☕ Донат (Boosty)</a> | "
        "<a href='https://yoomoney.ru/fundraise/1GS6R3MCH4R.260401' style='color:#00eeff; text-decoration:none;'>☕ ЮМани</a>"
    )
else:
    T_STATUS_ACTIVE = "Status: Active"
    T_STATUS_OFFLINE = "Status: Offline"
    T_STATUS_REC = "Status: Recording..."
    T_STATUS_PROC = "Status: Processing"
    T_STATUS_ERR = "Status: ERROR"
    T_READY = "Hotkeys Enabled"
    T_STANDBY = "System standby"
    T_LISTENING = "Listening to audio..."
    
    L_SETTINGS_TITLE = "SETTINGS"
    L_ENGINE = "RECOGNITION ENGINE"
    L_LANG = "DICTATION LANGUAGE"
    L_HOTKEY = "ACTIVATION HOTKEY"
    L_SAVE = "SAVE CHANGES"
    L_BTN_SETT = "⚙ SETTINGS"
    
    LINKS_TEXT = (
        "<a href='https://t.me/+FB4-Dd_lelJkNjJi' style='color:#00ffa3; text-decoration:none;'>TG Channel</a> | "
        "<a href='https://boosty.to/websansay/donate' style='color:#00eeff; text-decoration:none;'>Boosty</a> | "
        "<a href='https://yoomoney.ru/fundraise/1GS6R3MCH4R.260401' style='color:#00eeff; text-decoration:none;'>YooMoney</a>"
    )

# ================= LANGUAGES DATA =================
# key: ISO-639-1 code
LANGUAGES = {
    "ar": {"flag": "🇦🇪", "ru": "Арабский", "en": "Arabic"},
    "be": {"flag": "🇧🇾", "ru": "Белорусский", "en": "Belarusian"},
    "zh": {"flag": "🇨🇳", "ru": "Китайский", "en": "Chinese"},
    "nl": {"flag": "🇳🇱", "ru": "Нидерландский", "en": "Dutch"},
    "en": {"flag": "🇺🇸", "ru": "Английский", "en": "English"},
    "fr": {"flag": "🇫🇷", "ru": "Французский", "en": "French"},
    "de": {"flag": "🇩🇪", "ru": "Немецкий", "en": "German"},
    "he": {"flag": "🇮🇱", "ru": "Иврит", "en": "Hebrew"},
    "hi": {"flag": "🇮🇳", "ru": "Хинди", "en": "Hindi"},
    "it": {"flag": "🇮🇹", "ru": "Итальянский", "en": "Italian"},
    "ja": {"flag": "🇯🇵", "ru": "Японский", "en": "Japanese"},
    "kk": {"flag": "🇰🇿", "ru": "Казахский", "en": "Kazakh"},
    "ko": {"flag": "🇰🇷", "ru": "Корейский", "en": "Korean"},
    "pl": {"flag": "🇵🇱", "ru": "Польский", "en": "Polish"},
    "pt": {"flag": "🇵🇹", "ru": "Португальский", "en": "Portuguese"},
    "ru": {"flag": "🇷🇺", "ru": "Русский", "en": "Russian"},
    "es": {"flag": "🇪🇸", "ru": "Испанский", "en": "Spanish"},
    "sv": {"flag": "🇸🇪", "ru": "Шведский", "en": "Swedish"},
    "tt": {"flag": "🇷🇺", "ru": "Татарский", "en": "Tatar"},
    "tr": {"flag": "🇹🇷", "ru": "Турецкий", "en": "Turkish"},
    "uk": {"flag": "🇺🇦", "ru": "Украинский", "en": "Ukrainian"},
}

# ================= HOTKEY INPUT =================
class HotkeyInput(QLineEdit):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setReadOnly(True)
        self.setAlignment(Qt.AlignCenter)
        self.setFocusPolicy(Qt.StrongFocus)
        self.setCursor(Qt.ArrowCursor)

    def keyPressEvent(self, event: QKeyEvent):
        key = event.key()
        parts = []
        mods = event.modifiers()
        if mods & Qt.ControlModifier: parts.append("ctrl")
        if mods & Qt.AltModifier: parts.append("alt")
        if mods & Qt.ShiftModifier: parts.append("shift")
        if mods & Qt.MetaModifier: parts.append("win")
        
        # Если нажата не только клавиша-модификатор, добавим её саму
        if key not in (Qt.Key_Control, Qt.Key_Shift, Qt.Key_Alt, Qt.Key_Meta):
            key_name = ""
            if Qt.Key_A <= key <= Qt.Key_Z: key_name = chr(key).lower()
            elif Qt.Key_0 <= key <= Qt.Key_9: key_name = chr(key)
            elif Qt.Key_F1 <= key <= Qt.Key_F12: key_name = f"f{key - Qt.Key_F1 + 1}"
            elif key == Qt.Key_Space: key_name = "space"
            elif key == Qt.Key_Return or key == Qt.Key_Enter: key_name = "enter"
            elif key == Qt.Key_Escape: key_name = "esc"
            elif key == Qt.Key_Tab: key_name = "tab"
            
            if key_name:
                parts.append(key_name)
                
        if parts:
            self.setText("+".join(parts))

# ================= SETTINGS DIALOG =================
class SettingsDialog(QDialog):
    def __init__(self, config, on_save, parent=None):
        super().__init__(parent)
        self.config = config
        self.on_save = on_save
        
        self.setWindowTitle(L_SETTINGS_TITLE)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedSize(500, 680)
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(25, 25, 25, 25)
        
        self.frame = QFrame(self)
        self.frame.setStyleSheet("""
            QFrame {
                background-color: rgba(10, 15, 25, 240); 
                border-radius: 20px;
                border: 2px solid rgba(0, 200, 255, 80);
                border-top: 2px solid rgba(255, 255, 255, 90); 
            }
            QLabel {
                color: #e0e0e0;
                font-family: 'Segoe UI', sans-serif;
                font-size: 14px;
                font-weight: bold;
                border: none;
                background: transparent;
            }
            QComboBox, QLineEdit {
                background-color: rgba(20, 25, 40, 220);
                border: 1px solid rgba(0, 255, 255, 50);
                border-radius: 8px;
                color: #00eeff;
                padding: 10px;
                font-size: 14px;
                font-weight: bold;
            }
            QComboBox:focus, QLineEdit:focus {
                border: 2px solid rgba(0, 255, 255, 200);
                background-color: rgba(30, 40, 60, 240);
            }
            QComboBox QAbstractItemView {
                background-color: #0d121c;
                color: #00eeff;
                selection-background-color: rgba(0, 200, 255, 100);
                selection-color: white;
                border: 1px solid rgba(0, 200, 255, 80);
                outline: none;
            }
            QPushButton {
                background-color: rgba(0, 200, 255, 20);
                color: #ffffff;
                border: 1px solid rgba(0, 200, 255, 120);
                border-top: 1px solid rgba(255, 255, 255, 60);
                border-radius: 10px;
                padding: 12px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: rgba(0, 200, 255, 80);
            }
        """)
        
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(60)
        shadow.setColor(QColor(0, 200, 255, 180))
        shadow.setXOffset(0)
        shadow.setYOffset(0)
        self.frame.setGraphicsEffect(shadow)
        
        v_layout = QVBoxLayout(self.frame)
        v_layout.setContentsMargins(20, 20, 20, 20)
        v_layout.setAlignment(Qt.AlignCenter) 
        
        # TOP HEADER WITH CLOSE BUTTON
        header_layout = QHBoxLayout()
        header_layout.setAlignment(Qt.AlignCenter)
        
        lbl_title = QLabel(L_SETTINGS_TITLE)
        lbl_title.setStyleSheet("font-size: 18px; font-weight: 900; color: #ffffff; letter-spacing: 2px; border: none;")
        header_layout.addWidget(lbl_title, alignment=Qt.AlignCenter)
        
        # Кнопка закрытия окна абсолютно позиционирована
        self.btn_close = QPushButton("✕", self.frame)
        self.btn_close.setFixedSize(32, 32)
        self.btn_close.setCursor(Qt.PointingHandCursor)
        self.btn_close.setStyleSheet("""
            QPushButton {
                background: rgba(0, 0, 0, 80);
                border: 1px solid rgba(0, 0, 0, 200);
                border-bottom: 1px solid rgba(255, 255, 255, 30);
                color: #ff3366; font-size: 16px; font-weight: bold; border-radius: 16px;
            }
            QPushButton:hover { background: rgba(255, 50, 100, 50); color: #ffffff; }
        """)
        self.btn_close.clicked.connect(self.reject)
        # Отступ 20px сверху и справа (ширина frame = 450)
        self.btn_close.move(450 - 32 - 20, 20)
        
        v_layout.addLayout(header_layout)
        v_layout.addSpacing(20)
        
        # ENGINE
        lbl_engine = QLabel(L_ENGINE)
        v_layout.addWidget(lbl_engine, alignment=Qt.AlignCenter)
        
        self.opt_engine = QComboBox()
        self.opt_engine.setFixedWidth(200)
        self.opt_engine.addItems(["Groq", "Google"])
        self.opt_engine.setCurrentText(self.config.get("engine", "Groq"))
        v_layout.addWidget(self.opt_engine, alignment=Qt.AlignCenter)
        
        v_layout.addSpacing(15)
        
        # LANGUAGE
        lbl_lang = QLabel(L_LANG)
        v_layout.addWidget(lbl_lang, alignment=Qt.AlignCenter)
        
        self.opt_lang = QComboBox()
        self.opt_lang.setFixedWidth(240) # Slightly wider for flags
        
        # Режим Auto
        auto_label = "自动 (Auto)" if not is_ru else "Авто (Симтема)"
        if not is_ru: auto_label = "Auto (System)"
        self.opt_lang.addItem(auto_label, "Auto")
        
        # Сортируем языки по названию в зависимости от локали
        target_key = "ru" if is_ru else "en"
        sorted_lang_codes = sorted(LANGUAGES.keys(), key=lambda k: LANGUAGES[k][target_key])
        
        for code in sorted_lang_codes:
            data = LANGUAGES[code]
            label = f"{data['flag']} {data[target_key]}"
            self.opt_lang.addItem(label, code)
            
        # Устанавливаем текущий язык
        current_cfg_lang = self.config.get("language", "Auto")
        idx = self.opt_lang.findData(current_cfg_lang)
        if idx >= 0:
            self.opt_lang.setCurrentIndex(idx)
        else:
            self.opt_lang.setCurrentIndex(0)
            
        v_layout.addWidget(self.opt_lang, alignment=Qt.AlignCenter)
        
        # GROQ
        self.frame_groq = QFrame()
        self.frame_groq.setStyleSheet("border: none; background: transparent;")
        groq_layout = QVBoxLayout(self.frame_groq)
        groq_layout.setContentsMargins(0, 0, 0, 0)
        groq_layout.setAlignment(Qt.AlignCenter)
        
        groq_layout.addSpacing(15)
        lbl_key = QLabel("GROQ API KEY")
        groq_layout.addWidget(lbl_key, alignment=Qt.AlignCenter)
        
        self.entry_key = QLineEdit()
        self.entry_key.setFixedWidth(260)
        self.entry_key.setAlignment(Qt.AlignCenter)
        self.entry_key.setPlaceholderText("Secret key")
        self.entry_key.setEchoMode(QLineEdit.Password)
        self.entry_key.setText(decrypt_key(self.config.get("groq_api_key", "")))
        groq_layout.addWidget(self.entry_key, alignment=Qt.AlignCenter)
        
        lbl_link = QLabel("<a href='https://console.groq.com/keys' style='color:#00eeff; text-decoration:none;'>➜ Get Free Key</a>")
        lbl_link.setOpenExternalLinks(True)
        groq_layout.addWidget(lbl_link, alignment=Qt.AlignCenter)
        v_layout.addWidget(self.frame_groq, alignment=Qt.AlignCenter)
        
        self.opt_engine.currentTextChanged.connect(self.on_engine_change)
        
        v_layout.addSpacing(15)
        
        # HOTKEYS
        lbl_hk = QLabel(L_HOTKEY)
        v_layout.addWidget(lbl_hk, alignment=Qt.AlignCenter)
        
        self.entry_hotkey = HotkeyInput()
        self.entry_hotkey.setFixedWidth(200)
        self.entry_hotkey.setText(self.config.get("hotkey", "ctrl+alt"))
        v_layout.addWidget(self.entry_hotkey, alignment=Qt.AlignCenter)
        
        v_layout.addSpacing(15)
        
        # AUTOSTART
        self.chk_autostart = QCheckBox("Запускать вместе с Windows" if is_ru else "Launch at startup")
        self.chk_autostart.setChecked(self.config.get("autostart", False))
        self.chk_autostart.setStyleSheet("color: white; font-size: 14px;")
        v_layout.addWidget(self.chk_autostart, alignment=Qt.AlignCenter)
        
        v_layout.addSpacing(25)
        
        btn_save = QPushButton(L_SAVE)
        btn_save.setCursor(Qt.PointingHandCursor)
        btn_save.setFixedWidth(240)
        btn_save.clicked.connect(self.save_and_close)
        v_layout.addWidget(btn_save, alignment=Qt.AlignCenter)
        
        v_layout.addSpacing(15)
        
        lbl_about = QLabel(LINKS_TEXT)
        lbl_about.setAlignment(Qt.AlignCenter)
        lbl_about.setOpenExternalLinks(True)
        lbl_about.setStyleSheet("font-size: 12px; border: none; line-height: 1.5;")
        v_layout.addWidget(lbl_about, alignment=Qt.AlignCenter)
        
        main_layout.addWidget(self.frame)
        self.on_engine_change(self.opt_engine.currentText())

    def on_engine_change(self, choice):
        if choice == "Groq":
            self.frame_groq.show()
            self.setFixedSize(500, 780)
        else:
            self.frame_groq.hide()
            self.setFixedSize(500, 640)

    def save_and_close(self):
        self.config["engine"] = self.opt_engine.currentText()
        # Сохраняем ISO код, а не текстовую метку
        self.config["language"] = self.opt_lang.currentData()
        self.config["groq_api_key"] = encrypt_key(self.entry_key.text().strip())
        self.config["hotkey"] = self.entry_hotkey.text().strip()
        self.config["autostart"] = self.chk_autostart.isChecked()
        self.on_save(self.config)
        self.accept()


# ================= WIDGETS =================
class AudioWaveVisualizer(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(220, 120)  # Убеждаемся что ширина больше нуля
        self.is_recording = False
        self.phase = 0.0
        
        self.target_volume = 0.0
        self.smoothed_volume = 0.0
        self.time_t = 0.0
        
        self.volume_getter = None
        self.is_active_app = True
        
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_waves)
        self.timer.start(30)
        
    def set_active(self, state: bool):
        self.is_active_app = state
        self.update()

    def set_volume_getter(self, getter):
        self.volume_getter = getter

    def set_recording(self, state: bool):
        self.is_recording = state
        if not state:
            self.target_volume = 0.0
            
    def set_volume(self, vol: float):
        # Гиперчувствительность стала еще выше (x100)
        self.target_volume = min(1.0, vol * 100.0)
        
    def update_waves(self):
        speed = 0.15 if self.is_recording else 0.03
        self.phase += speed
        self.time_t += 0.05
        
        if self.volume_getter and self.is_recording:
            self.set_volume(self.volume_getter())
            
        # Плавное сглаживание амплитуды звука
        self.smoothed_volume += (self.target_volume - self.smoothed_volume) * 0.4
        self.update() 
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        w = self.width()
        h = self.height()
        mid_y = h / 2.0
        
        if not self.is_active_app:
            idle_amp = 0.0
            current_amp = 0.0
        else:
            idle_amp = h / 4.5
            active_amp = idle_amp + (h / 2.2) * self.smoothed_volume
            current_amp = active_amp if self.is_recording else idle_amp
        
        lines_count = 14
        for i in range(lines_count):
            path = QPainterPath()
            path.moveTo(0, mid_y)
            
            freq_mod = 0.015 + (i * 0.003)
            phase_offset = self.phase + (i * 0.4)
            # Разброс высот волн больше (от 40% до 100% current_amp)
            amp_mod = current_amp * (0.4 + 0.6 * math.sin(i * 1.5 + self.time_t))

            for x in range(0, w, 5):
                envelope = math.sin((x / w) * math.pi)
                val = math.sin(x * freq_mod + phase_offset) * amp_mod * envelope
                y = mid_y + val
                path.lineTo(x, y)
                
            if not self.is_active_app:
                # В спящем режиме будет одна "дышащая" неоновая линия (режим Standby)
                if i != lines_count // 2:
                    continue
                pulse_alpha = int(60 + 40 * math.sin(self.time_t * 1.5))
                color = QColor(0, 200, 255, pulse_alpha)
                painter.setPen(QPen(color, 2.0))
                painter.drawPath(path)
                continue
                
            ratio = i / float(lines_count - 1)
            r = int(0 * (1 - ratio) + 200 * ratio)
            g = int(255 * (1 - ratio) + 0 * ratio)
            b = 255
            
            # Более яркие и толстые линии для массивного вида
            alpha = 180 if self.is_recording else 60
            color = QColor(r, g, b, alpha)
                
            painter.setPen(QPen(color, 2.5))
            painter.drawPath(path)

class CyberToggle(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(160, 64)
        self._checked = True
        
        self.max_x = self.width() - 8 - (self.height() - 16)
        self._pos = self.max_x if self._checked else 8
        
        self.anim = QPropertyAnimation(self, b"pos_val")
        self.anim.setDuration(400)
        self.anim.setEasingCurve(QEasingCurve.OutElastic)
        
        self.toggled_callback = None
        self.setCursor(Qt.PointingHandCursor)
        
    def get_pos_val(self): return self._pos
    def set_pos_val(self, val):
        self._pos = val
        self.update()
        
    pos_val = Property(float, get_pos_val, set_pos_val)
    
    def mousePressEvent(self, event):
        self._checked = not self._checked
        self.anim.stop()
        self.anim.setStartValue(self._pos)
        self.anim.setEndValue(self.max_x if self._checked else 8)
        self.anim.start()
        
        if self.toggled_callback:
            self.toggled_callback(self._checked)
            
    def set_checked(self, state):
        self._checked = state
        self._pos = self.max_x if state else 8
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        w = self.width()
        h = self.height()
        bg_rect = QRectF(0, 0, w, h)
        
        if self._checked:
            bloom_grad = QRadialGradient(w/2, h/2, w)
            bloom_grad.setColorAt(0.0, QColor(0, 255, 120, 80))
            bloom_grad.setColorAt(1.0, QColor(0, 255, 120, 0))
            painter.setBrush(bloom_grad)
            painter.setPen(Qt.NoPen)
            painter.drawRoundedRect(bg_rect, h/2, h/2)
        
        base_grad = QLinearGradient(0, 0, 0, h)
        base_grad.setColorAt(0, QColor(25, 30, 45, 230))
        base_grad.setColorAt(1, QColor(5, 8, 15, 230))
        painter.setBrush(base_grad)
        painter.drawRoundedRect(bg_rect, h/2, h/2)
        
        bevel_rect = QRectF(2, 2, w-4, h/2)
        bevel_grad = QLinearGradient(0, 2, 0, h/2)
        bevel_grad.setColorAt(0, QColor(255, 255, 255, 100))
        bevel_grad.setColorAt(1, QColor(255, 255, 255, 0))
        painter.setBrush(bevel_grad)
        painter.drawRoundedRect(bevel_rect, h/2-2, h/2-2)

        if self._checked:
            track_color = QColor(0, 255, 120, 255)
            text_color = QColor(0, 255, 120, 255)
            text_str = "ON"
            inner_glow = QColor(0, 255, 120, 50)
        else:
            track_color = QColor(100, 100, 100, 200)
            text_color = QColor(120, 120, 120, 255)
            text_str = "OFF"
            inner_glow = Qt.NoBrush
            
        track_rect = QRectF(1, 1, w-2, h-2)
        painter.setPen(QPen(track_color, 1.5))
        painter.setBrush(inner_glow)
        painter.drawRoundedRect(track_rect, h/2-1, h/2-1)
        
        font = QFont("Segoe UI", 16, QFont.Bold)
        painter.setFont(font)
        text_r = QRectF(20, 0, w/2, h) if self._checked else QRectF(w/2 - 10, 0, w/2, h)
        
        painter.setPen(QColor(0,0,0,200)) 
        painter.drawText(text_r.translated(0, 1), Qt.AlignCenter, text_str)
        painter.setPen(text_color)
        painter.drawText(text_r, Qt.AlignCenter, text_str)
        
        knob_w = h - 16 
        knob_rect = QRectF(self._pos, 8, knob_w, knob_w)
        
        grad = QRadialGradient(knob_rect.center().x(), knob_rect.y() + knob_w/4, knob_w/1.2)
        grad.setColorAt(0.0, QColor(255, 255, 255))
        grad.setColorAt(0.3, QColor(200, 210, 220))
        grad.setColorAt(0.8, QColor(100, 110, 120, 250))
        grad.setColorAt(1.0, QColor(40, 50, 60, 250))
        
        painter.setBrush(grad)
        painter.setPen(QPen(QColor(10, 10, 20), 1))
        painter.drawEllipse(knob_rect)

class FuturisticWidget(QWidget):
    def __init__(self, config, on_config_save, on_toggle, on_quit):
        super().__init__()
        self.config = config
        self.on_config_save = on_config_save
        self.on_toggle = on_toggle
        self.on_quit = on_quit
        
        self.is_active = True
        self.is_hovered = False
        
        self.W = 260
        self.H = 540
        
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        screen = QApplication.primaryScreen().geometry()
        self.pos_y = int(screen.height() / 2 - self.H / 2)
        self.pos_x_hidden = screen.width() - 15
        self.pos_x_expanded = screen.width() - self.W
        
        self.setGeometry(self.pos_x_hidden, self.pos_y, self.W, self.H)
        
        self.led_phase = 0
        self.led_timer = QTimer(self)
        self.led_timer.timeout.connect(self.update_leds)
        self.led_timer.start(50)
        
        self.build_ui()
        self.setup_tray()

    def update_leds(self):
        self.led_phase += 1
        self.update() 

    def build_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15) 
        main_layout.setAlignment(Qt.AlignCenter)
        
        self.inner_frame = QFrame(self)
        main_layout.addWidget(self.inner_frame)
        
        v_layout = QVBoxLayout(self.inner_frame)
        v_layout.setContentsMargins(20, 30, 20, 30)
        v_layout.setAlignment(Qt.AlignCenter)
        
        lbl_title = QLabel("WS WHISPER")
        lbl_title.setAlignment(Qt.AlignCenter)
        lbl_title.setStyleSheet("""
            color: white; font-weight: 900; font-family: 'Segoe UI', sans-serif; 
            font-size: 20px; letter-spacing: 2px; border: none; background: transparent;
        """)
        v_layout.addWidget(lbl_title, alignment=Qt.AlignCenter)
        v_layout.addSpacing(40)
        
        self.btn_toggle = CyberToggle()
        self.btn_toggle.toggled_callback = self.toggle_state
        v_layout.addWidget(self.btn_toggle, alignment=Qt.AlignCenter)
        v_layout.addSpacing(40)
        
        self.lbl_status = QLabel(T_STATUS_ACTIVE.upper())
        self.lbl_status.setAlignment(Qt.AlignCenter)
        self.lbl_status.setStyleSheet("""
            color: #00FFA3; font-weight: 900; font-size: 16px; font-family: 'Segoe UI'; 
            letter-spacing: 1px; border: none; background: transparent;
        """)
        v_layout.addWidget(self.lbl_status, alignment=Qt.AlignCenter)
        
        self.lbl_details = QLabel(T_READY)
        self.lbl_details.setAlignment(Qt.AlignCenter)
        self.lbl_details.setStyleSheet("""
            color: #aaaaaa; font-size: 13px; font-weight: 600; font-family: 'Segoe UI'; 
            border: none; background: transparent;
        """)
        v_layout.addWidget(self.lbl_details, alignment=Qt.AlignCenter)
        
        v_layout.addSpacing(25)
        
        self.btn_settings = QPushButton(L_BTN_SETT)
        self.btn_settings.setFixedSize(140, 35)
        self.btn_settings.setCursor(Qt.PointingHandCursor)
        self.btn_settings.setStyleSheet("""
            QPushButton { 
                background: rgba(0, 200, 255, 10); 
                border: 1px solid rgba(0, 200, 255, 60); 
                border-top: 1px solid rgba(255, 255, 255, 40);
                border-radius: 6px; color: #ffffff; font-size: 12px; font-weight: bold;
                letter-spacing: 1px; font-family: 'Segoe UI';
            } 
            QPushButton:hover { 
                background: rgba(0, 200, 255, 40); border: 1px solid rgba(0, 200, 255, 255);
            }
        """)
        self.btn_settings.clicked.connect(self.open_settings)
        v_layout.addWidget(self.btn_settings, alignment=Qt.AlignCenter)
        
        v_layout.addSpacing(30)
        
        self.visualizer = AudioWaveVisualizer()
        v_layout.addWidget(self.visualizer, alignment=Qt.AlignCenter)
        
        self.anim = QPropertyAnimation(self, b"geometry")
        self.anim.setDuration(400)
        self.anim.setEasingCurve(QEasingCurve.OutExpo)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        w = self.width()
        h = self.height()
        rect = QRectF(15, 15, w-30, h-30)
        
        painter.setBrush(QColor(10, 15, 25, 240)) 
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(rect, 20, 20)
        
        rim_grad = QLinearGradient(rect.topLeft(), rect.bottomRight())
        rim_grad.setColorAt(0, QColor(0, 200, 255, 255)) 
        rim_grad.setColorAt(1, QColor(140, 0, 255, 255)) 
        painter.setPen(QPen(rim_grad, 2))
        painter.setBrush(Qt.NoBrush)
        painter.drawRoundedRect(rect, 20, 20)
        
        painter.setPen(QPen(QColor(0, 200, 255, 40), 6))
        painter.drawRoundedRect(rect, 20, 20)
        
        specular_rect = QRectF(16, 16, w-32, h/3)
        spec_grad = QLinearGradient(0, 16, 0, 16 + h/3)
        spec_grad.setColorAt(0, QColor(255, 255, 255, 70))
        spec_grad.setColorAt(1, QColor(255, 255, 255, 0))
        painter.setPen(Qt.NoPen)
        painter.setBrush(spec_grad)
        
        path = QPainterPath()
        path.addRoundedRect(16, 16, w-32, h-32, 19, 19)
        painter.setClipPath(path)
        painter.drawRect(specular_rect)
        painter.setClipping(False)

        led_y = h - 145
        led_count = 10
        spacing = 8
        total_w = (led_count * 4) + ((led_count - 1) * spacing)
        led_start_x = (w - total_w) / 2
        
        for i in range(led_count):
            x = led_start_x + i * (4 + spacing)
            dist = abs((self.led_phase % 60) - (i * 3))
            base_glow = max(40, 255 - dist * 15) if self.btn_toggle._checked else 40
            
            painter.setBrush(QColor(0, int(base_glow*0.8), int(base_glow), base_glow))
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(QRectF(x, led_y, 4, 4))
            
    def toggle_state(self, is_on):
        self.is_active = is_on
        self.visualizer.set_active(is_on)
        if self.is_active:
            self.lbl_status.setText(T_STATUS_ACTIVE.upper())
            self.lbl_status.setStyleSheet("color: #00FFA3; font-weight: 900; font-size: 16px; letter-spacing: 1px;")
            self.lbl_details.setText(T_READY)
        else:
            self.lbl_status.setText(T_STATUS_OFFLINE.upper())
            self.lbl_status.setStyleSheet("color: #888888; font-weight: 900; font-size: 16px; letter-spacing: 1px;")
            self.lbl_details.setText(T_STANDBY)
            
        self.on_toggle(self.is_active)

    def enterEvent(self, event):
        self.is_hovered = True
        self.anim.stop()
        self.anim.setStartValue(self.geometry())
        self.anim.setEndValue(QRect(self.pos_x_expanded, self.pos_y, self.W, self.H))
        self.anim.start()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.is_hovered = False
        QTimer.singleShot(200, self.check_leave)
        super().leaveEvent(event)

    def check_leave(self):
        if not self.is_hovered:
            self.anim.stop()
            self.anim.setStartValue(self.geometry())
            self.anim.setEndValue(QRect(self.pos_x_hidden, self.pos_y, self.W, self.H))
            self.anim.start()

    def set_status(self, text):
        if "[REC]" in text:
            self.lbl_status.setText(T_STATUS_REC.upper())
            self.lbl_status.setStyleSheet("color: #00FFA3;")
            self.lbl_details.setText(T_LISTENING)
            self.visualizer.set_recording(True)
        elif "Обработка" in text or "Распознавание" in text:
            self.lbl_status.setText(T_STATUS_PROC.upper())
            self.lbl_status.setStyleSheet("color: #00eeff;")
            self.lbl_details.setText(text) # Show internal message in details
            self.visualizer.set_recording(False)
        elif "Вставлено" in text:
            self.lbl_details.setText(text)
            self.lbl_status.setText(T_STATUS_ACTIVE.upper())
            self.lbl_status.setStyleSheet("color: #00FFA3;")
            self.visualizer.set_recording(False)
            QTimer.singleShot(3000, lambda: self.lbl_details.setText(T_READY))
        elif "ОШИБКА" in text:
            self.lbl_status.setText(T_STATUS_ERR.upper())
            self.lbl_status.setStyleSheet("color: #FF2E63;")
            self.lbl_details.setText(text)
            self.visualizer.set_recording(False)
            QTimer.singleShot(4000, lambda: self.lbl_details.setText(T_READY))
        else:
            # Для "Слишком тихо", или любых других сообщений
            self.lbl_status.setText(T_STATUS_ACTIVE.upper())
            self.lbl_status.setStyleSheet("color: #00FFA3;")
            self.lbl_details.setText(text)
            self.visualizer.set_recording(False)
            QTimer.singleShot(3000, lambda: self.lbl_details.setText(T_READY))

    def open_settings(self):
        self.is_hovered = True
        dialog = SettingsDialog(self.config, self.on_config_save, self)
        dialog.exec()
        self.is_hovered = False
        self.check_leave()

    def get_tray_icon(self):
        if os.path.exists(LOGO_PATH):
            return QIcon(LOGO_PATH)
        else:
            pixmap = QPixmap(64, 64)
            pixmap.fill(Qt.transparent)
            painter = QPainter(pixmap)
            painter.setRenderHint(QPainter.Antialiasing)
            painter.setBrush(QBrush(QColor("#00eeff")))
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(10, 10, 44, 44)
            painter.end()
            return QIcon(pixmap)

    def setup_tray(self):
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(self.get_tray_icon())
        self.tray_icon.setToolTip("WS Whisper")
        menu = QMenu()
        menu.setStyleSheet("QMenu { background-color: #0a050f; color: white; border: 1px solid #30363d;} QMenu::item:selected { background-color: #00eeff; color: black;}")
        quit_action = menu.addAction("Полный Выход")
        quit_action.triggered.connect(self.quit_app)
        self.tray_icon.setContextMenu(menu)
        self.tray_icon.show()

    def quit_app(self):
        self.tray_icon.hide()
        self.on_quit()
        QCoreApplication.quit()
