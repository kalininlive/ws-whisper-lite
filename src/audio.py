import sounddevice as sd
import numpy as np
import threading

class AudioRecorder:
    def __init__(self, sample_rate=16000, channels=1):
        self.sample_rate = sample_rate
        self.channels = channels
        self.recording = False
        self.stream = None
        self.audio_data = []
        self.current_volume = 0.0
        self._lock = threading.Lock()

    def _callback(self, indata, frames, time, status):
        if status:
            print(f"Audio status: {status}")
        with self._lock:
            if self.recording:
                self.audio_data.append(indata.copy())
                self.current_volume = float(np.max(np.abs(indata)))
            else:
                self.current_volume = 0.0

    def start(self):
        with self._lock:
            self.audio_data.clear()
            self.current_volume = 0.0
            self.recording = True
        
        # Запускаем неблокирующий поток записи float32 16kHz Mono
        self.stream = sd.InputStream(samplerate=self.sample_rate, 
                                     channels=self.channels,
                                     dtype='float32',
                                     callback=self._callback)
        self.stream.start()

    def stop(self):
        with self._lock:
            self.recording = False
            self.current_volume = 0.0
        if self.stream:
            self.stream.stop()
            self.stream.close()
            self.stream = None
        
        with self._lock:
            if self.audio_data:
                # Объединяем все записанные отрезки в единый плоский массив float32 (требование whisper)
                full_audio = np.concatenate(self.audio_data, axis=0).flatten()
                print(f"[AUDIO] Записано {len(full_audio)/self.sample_rate:.2f} сек, Макс. амплитуда: {np.max(np.abs(full_audio)):.4f}")
                return full_audio
            else:
                return np.array([], dtype='float32')
