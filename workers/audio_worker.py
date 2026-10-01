"""
AudioWorker - mikrofondan real vaqtda ovoz oladi va Vosk yordamida matnga
o'giradi. Natijalarni Signal orqali Main Thread'ga yuboradi (SRS 5-band).

MUHIM: Vosk'ning KaldiRecognizer obyekti Thread-xavfsiz emas. Avvalgi
versiyada `reset_recognizer()`/`resume_listening()` asosiy (GUI) Thread'dan
to'g'ridan-to'g'ri `self._recognizer.Reset()` ni chaqirar edi, shu payt esa
shu obyektning o'zi fon Thread'dagi `run()` ichida `AcceptWaveform()` orqali
band bo'lishi mumkin edi. Bu poyga holati (race condition) Vosk dekoderining
ichki holatini buzib, "Failed to process waveform" xatosiga va dasturning
qulashiga sabab bo'lgan. Endi Reset() so'rovi faqat bayroq orqali beriladi va
uni FAQAT shu Thread'ning o'zi, `run()` sikli ichida bajaradi.

YANA BIR MUHIM NUQTA: `text_recognized` signali endi (matn, is_final) juftini
yuboradi. Buning sababi - avval PARTIAL (hali tugallanmagan) natijalar ham
xato sifatida hisoblanar edi: masalan, "salom" so'zini TO'G'RI aytayotganda
ham, Vosk uni "s", "sa", "sal"... deb bosqichma-bosqich chiqaradi, va bu
oraliq bo'laklar hali to'liq so'zga mos kelmasligi tabiiy holat, xato emas.
Shu sabab bitta to'g'ri urinish ichida hisoblagich soxta ravishda 5gacha
yetib qolishi mumkin edi. Endi: PARTIAL natijalar faqat TEZ ijobiy moslikni
(so'z to'g'ri aytilganini) aniqlash uchun ishlatiladi (500ms talabini
saqlash uchun), FINAL natija (Vosk butun urinishni yakunlaganda) esa xato
hisoblagichini oshirish uchun ishlatiladi - chunki bu haqiqatan tugallangan,
noto'g'ri chiqqan bitta urinishni bildiradi.
"""

import json

import pyaudio
from PyQt6.QtCore import QThread, pyqtSignal
from vosk import KaldiRecognizer, Model

from config import AUDIO_CHANNELS, AUDIO_CHUNK_SIZE, AUDIO_SAMPLE_RATE


class AudioWorker(QThread):
    # (matn, yakuniy_natijami) - partial natijalar tez fikr-mulohaza (to'g'ri
    # o'qilganda darhol yashilga o'tishi) uchun, final natijalar esa xato
    # hisoblash uchun ishlatiladi (pastga qarang: nima uchun ajratilgan).
    text_recognized = pyqtSignal(str, bool)
    # Model yuklanmasa, mikrofon ochilmasa yoki tahlilda xato bo'lsa signal
    error_occurred = pyqtSignal(str)

    def __init__(self, model_path: str, parent=None):
        super().__init__(parent)
        self._model_path = model_path
        self._running = False
        self._paused = False
        self._reset_requested = False
        self._model = None
        self._recognizer = None

    def run(self):
        try:
            self._model = Model(self._model_path)
            self._recognizer = KaldiRecognizer(self._model, AUDIO_SAMPLE_RATE)
        except Exception as exc:  # noqa: BLE001
            self.error_occurred.emit(
                f"Vosk modelini yuklashda xato ({self._model_path}): {exc}"
            )
            return

        audio_interface = pyaudio.PyAudio()
        try:
            stream = audio_interface.open(
                format=pyaudio.paInt16,
                channels=AUDIO_CHANNELS,
                rate=AUDIO_SAMPLE_RATE,
                input=True,
                frames_per_buffer=AUDIO_CHUNK_SIZE,
            )
        except Exception as exc:  # noqa: BLE001
            self.error_occurred.emit(f"Mikrofonni ochishda xato: {exc}")
            audio_interface.terminate()
            return

        self._running = True
        stream.start_stream()

        while self._running:
            # Reset so'rovi bo'lsa, uni FAQAT shu Thread ichida, xavfsiz
            # tarzda bajaramiz (boshqa Thread'dan to'g'ridan-to'g'ri
            # recognizer'ga tegilmaydi).
            if self._reset_requested:
                self._reset_requested = False
                self._safe_reset()

            if self._paused:
                self.msleep(50)
                continue

            data = stream.read(AUDIO_CHUNK_SIZE, exception_on_overflow=False)

            try:
                accepted = self._recognizer.AcceptWaveform(data)
            except Exception as exc:  # noqa: BLE001
                # Kutilmagan holatda dekoderni butunlay qayta yaratamiz,
                # shunda bitta xato butun dasturni yiqitmaydi.
                self.error_occurred.emit(f"Nutqni tahlil qilishda vaqtinchalik xato: {exc}")
                self._recreate_recognizer()
                continue

            if accepted:
                result = json.loads(self._recognizer.Result())
                text = result.get("text", "")
                if text:
                    self.text_recognized.emit(text, True)
            else:
                partial = json.loads(self._recognizer.PartialResult())
                text = partial.get("partial", "")
                if text:
                    self.text_recognized.emit(text, False)

        stream.stop_stream()
        stream.close()
        audio_interface.terminate()

    def _safe_reset(self):
        try:
            self._recognizer.Reset()
        except Exception:  # noqa: BLE001
            self._recreate_recognizer()

    def _recreate_recognizer(self):
        try:
            self._recognizer = KaldiRecognizer(self._model, AUDIO_SAMPLE_RATE)
        except Exception as exc:  # noqa: BLE001
            self.error_occurred.emit(f"Recognizer'ni qayta yaratishda xato: {exc}")

    # ------------------------------------------------------------------ #
    # Boshqa Thread'lardan (masalan, KaraokeController, GUI Thread) chaqiriladi.
    # Bu metodlar recognizer'ga BEVOSITA tegmaydi — faqat bayroq qo'yadi,
    # haqiqiy ish esa yuqoridagi run() sikli ichida, shu Thread'ning o'zida
    # bajariladi.
    # ------------------------------------------------------------------ #
    def pause_listening(self):
        """Mikrofonni vaqtincha to'xtatadi (TTS yordami ijro etilayotganda, SRS 3.3)."""
        self._paused = True

    def resume_listening(self):
        """Mikrofonni qaytadan faollashtiradi va tanish holatini tozalashni so'raydi."""
        self._reset_requested = True
        self._paused = False

    def reset_recognizer(self):
        """Joriy so'z uchun tanish natijalarini tozalashni so'raydi (keyingi so'zga o'tishda)."""
        self._reset_requested = True

    def stop(self):
        self._running = False
        self.wait(2000)
