"""
OfflineTTSSynthesizer - espeak-ng orqali TO'LIQ OFLAYN matnni audio faylga
aylantiradi (internetga umuman muhtoj emas).

Bu klass workers/tts_worker.py dagi TTSSynthesizer bilan bir xil ochiq
interfeysga ega (`synthesis_ready(str)` / `error_occurred(str)` signallari),
shuning uchun KaraokeController ikkalasini ham bir xil tarzda ishlata oladi
va foydalanuvchi ular orasida GUI orqali erkin almashishi mumkin.

espeak-ng alohida tizim dasturi sifatida o'rnatilishi kerak (pip orqali
o'rnatilmaydi):
    Linux:   sudo apt install espeak-ng
    Windows: https://github.com/espeak-ng/espeak-ng/releases

espeak-ng "formant sintez" usulidan foydalanadi - ovoz mexanikroq eshitiladi,
lekin talaffuz aniq va tushunarli chiqadi, hech qanday tarmoq yoki katta
model fayllarini yuklab olishni talab qilmaydi.
"""

import os
import shutil
import subprocess
import uuid

from PyQt6.QtCore import QThread, pyqtSignal

from config import TEMP_AUDIO_DIR

_SYNTHESIS_TIMEOUT_SECONDS = 15


class OfflineTTSSynthesizer(QThread):
    synthesis_ready = pyqtSignal(str)     # tayyor bo'lgan audio (.wav) fayl yo'li
    error_occurred = pyqtSignal(str)

    def __init__(self, text: str, voice: str, wpm: int = 150, pitch: int = 50, parent=None):
        super().__init__(parent)
        self._text = text
        self._voice = voice
        self._wpm = wpm
        self._pitch = pitch

    def run(self):
        if shutil.which("espeak-ng") is None:
            self.error_occurred.emit(
                "espeak-ng topilmadi. O'rnatish uchun terminalda: "
                "sudo apt install espeak-ng (Windows uchun README'ga qarang)."
            )
            return

        file_path = os.path.join(TEMP_AUDIO_DIR, f"{uuid.uuid4().hex}.wav")
        command = [
            "espeak-ng",
            "-v", self._voice,
            "-s", str(self._wpm),
            "-p", str(self._pitch),
            "-w", file_path,
            self._text,
        ]

        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=_SYNTHESIS_TIMEOUT_SECONDS,
            )
        except subprocess.TimeoutExpired:
            self.error_occurred.emit("espeak-ng vaqt tugadi (juda uzoq ishladi).")
            return
        except Exception as exc:  # noqa: BLE001
            self.error_occurred.emit(f"Offline ovozli yordamda xato: {exc}")
            return

        if result.returncode != 0:
            self.error_occurred.emit(f"espeak-ng xatosi: {result.stderr.strip()}")
            return

        self.synthesis_ready.emit(file_path)
