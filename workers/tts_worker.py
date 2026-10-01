"""
TTSSynthesizer - edge-tts orqali matnni audio faylga aylantiradi (FAQAT
sintez qiladi, ijro ETMAYDI).

Muhim arxitektura eslatmasi: audio ijrosi (QMediaPlayer) doim asosiy (GUI)
Thread'da, VoxTilController ichidagi bitta umumiy player orqali amalga
oshiriladi. Avvalgi versiyada QMediaPlayer har safar shu fon Thread ichida
yaratilgan edi — bu bir necha marta ketma-ket ishlatilganda beqarorlik va
"Segmentation fault" ga olib kelgan edi. Shuning uchun bu klass endi faqat
tarmoq orqali audio faylni tayyorlaydi va uni asosiy Thread'ga topshiradi.
"""

import asyncio
import os
import uuid

import edge_tts
from PyQt6.QtCore import QThread, pyqtSignal

from config import TEMP_AUDIO_DIR

# Internet umuman ishlamasa ham dastur cheksiz kutib qolmasligi uchun
# sintezga qat'iy vaqt chegarasi (soniyalarda).
_SYNTHESIS_TIMEOUT_SECONDS = 15


class TTSSynthesizer(QThread):
    synthesis_ready = pyqtSignal(str)     # tayyor bo'lgan audio fayl yo'li
    error_occurred = pyqtSignal(str)

    def __init__(self, text: str, voice: str, rate: str = "+0%", pitch: str = "+0Hz", parent=None):
        super().__init__(parent)
        self._text = text
        self._voice = voice
        self._rate = rate
        self._pitch = pitch

    def run(self):
        file_path = os.path.join(TEMP_AUDIO_DIR, f"{uuid.uuid4().hex}.mp3")
        try:
            asyncio.run(self._synthesize(file_path))
        except asyncio.TimeoutError:
            self.error_occurred.emit(
                "Ovozli yordam uchun serverga ulanib bo'lmadi (vaqt tugadi). "
                "Internet aloqasini tekshiring."
            )
            return
        except Exception as exc:  # noqa: BLE001
            self.error_occurred.emit(f"Ovozli yordamda xato: {exc}")
            return
        self.synthesis_ready.emit(file_path)

    async def _synthesize(self, file_path: str):
        communicate = edge_tts.Communicate(
            self._text, self._voice, rate=self._rate, pitch=self._pitch
        )
        await asyncio.wait_for(communicate.save(file_path), timeout=_SYNTHESIS_TIMEOUT_SECONDS)
