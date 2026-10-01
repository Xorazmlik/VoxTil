"""
VoxTilController - UI va Worker Thread'lar orasidagi asosiy mantiqni boshqaradi.
Bu klass "beynini" tashkil etadi: so'zlar ro'yxati, joriy holat, xatolar
hisoblagichi va TTS yordamining ishga tushishi shu yerda nazorat qilinadi.

MUHIM: audio ijrosi (QMediaPlayer) doim shu klass ichida, bitta umumiy
player orqali, asosiy (GUI) Thread'da amalga oshiriladi. Faqat tarmoq orqali
audio sintez qilish (edge-tts) fon Thread'ida (TTSSynthesizer) bajariladi.
Bu ikkalasini aralashtirib yuborish (playback'ni fon Thread'ida ochish)
beqarorlik va "Segmentation fault"ga olib kelishi mumkin edi (v1 dagi xato).

YANA BIR MUHIM NUQTA: har bir TTSSynthesizer/AudioWorker `parent=self` bilan
yaratiladi va `finished` signali `deleteLater()`ga ulanadi. Sababi - agar
QThread obyekti hech qanday Qt ota-obyektiga (parent) bog'lanmasa, uning
umri faqat Python o'zgaruvchisi (masalan, `self._pregen_synth`) orqali
saqlanadi; keyingi so'z uchun yangi obyekt yaratilib shu o'zgaruvchiga
qayta yozilganda, ESKI obyekt hali to'liq to'xtamagan bo'lishi mumkin bo'lsa
ham, Python uni darhol "chiqindi" deb hisoblab o'chirishga urinadi - bu
"QThread: Destroyed while thread is still running" xatosi va dasturning
qulashiga olib kelgan (ayniqsa fonda ko'plab so'zlar tez-tez ketma-ket
tayyorlanayotgan pre-generation vaqtida). `parent=self` C++ darajasida
obyektni tirik saqlaydi, `finished->deleteLater` esa uni FAQAT thread
haqiqatan to'xtagandan keyin xavfsiz tarzda tozalaydi.

YANA BIR NUQTA (2-bosqichdan keyin qo'shildi): TTS ikki xil manbadan
ishlashi mumkin - ONLAYN (`workers/tts_worker.py`, edge-tts, internet talab
qiladi, ovoz sifati yuqoriroq) va OFFLINE (`workers/offline_tts_worker.py`,
espeak-ng, internetga umuman muhtoj emas, ovoz mexanikroq). Ikkalasi ham bir
xil signal interfeysiga ega, shuning uchun `_make_synthesizer()` orqali
qaysi biri tanlanganidan qat'iy nazar qolgan kod o'zgarishsiz ishlayveradi.
"""

import os

from PyQt6.QtCore import QObject, QTimer, QUrl, pyqtSignal
from PyQt6.QtMultimedia import QAudioOutput, QMediaPlayer

from config import (
    DEFAULT_LANGUAGE,
    DEFAULT_SPEED_PERCENT,
    DEFAULT_TTS_MODE,
    ERROR_LIMIT,
    ESPEAK_BASE_WPM,
    ESPEAK_MAX_WPM,
    ESPEAK_MIN_WPM,
    LANGUAGES,
    MATCH_LOOKBACK,
    MAX_SPEED_PERCENT,
    MIN_SPEED_PERCENT,
    OFFLINE_HELP_PITCH,
    OFFLINE_NORMAL_PITCH,
    TTS_PITCH,
)
from utils.matcher import is_match, last_word
from utils.network import is_internet_available
from utils.text_processor import tokenize_text
from workers.audio_worker import AudioWorker
from workers.offline_tts_worker import OfflineTTSSynthesizer
from workers.tts_worker import TTSSynthesizer


class VoxTilController(QObject):
    word_status_changed = pyqtSignal(int, str)   # (so'z indeksi, holat: "current"/"done"/"pending")
    status_message = pyqtSignal(str)
    session_finished = pyqtSignal(dict)          # umumiy statistika (SRS 7-band, 7-qadam)
    internet_status_changed = pyqtSignal(bool)
    pre_listen_busy_changed = pyqtSignal(bool)   # UI shu orqali tugmani band/bo'sh qiladi

    def __init__(self, parent=None):
        super().__init__(parent)
        self.display_tokens: list[str] = []
        self.words: list[str] = []
        self.current_index = 0
        self.error_counts: dict[int, int] = {}
        self.language = DEFAULT_LANGUAGE
        self.speed_percent = DEFAULT_SPEED_PERCENT
        self.tts_mode = DEFAULT_TTS_MODE   # "online" (edge-tts) yoki "offline" (espeak-ng)
        self.audio_worker: AudioWorker | None = None
        self._session_active = False

        # --- Audio ijrosi: bitta umumiy player, doim asosiy Thread'da ---
        self._media_player = QMediaPlayer(self)
        self._audio_output = QAudioOutput(self)
        self._media_player.setAudioOutput(self._audio_output)
        self._media_player.mediaStatusChanged.connect(self._on_media_status_changed)
        self._media_player.errorOccurred.connect(self._on_media_error)
        self._playback_kind: str | None = None   # "help" yoki "pre_listen"
        self._playback_file: str | None = None

        # Ba'zi tizimlarda (masalan, audio qurilmasi noto'g'ri sozlangan bo'lsa)
        # QMediaPlayer hech qanday "tugadi" signalini bermasligi mumkin. Shunday
        # holatda `_tts_busy` abadiy True bo'lib qolib, ovozli yordam butunlay
        # ishlamay qo'yishining oldini olish uchun soqchi-timer (watchdog):
        self._playback_watchdog = QTimer(self)
        self._playback_watchdog.setSingleShot(True)
        self._playback_watchdog.timeout.connect(self._on_playback_timeout)

        self._synth_worker: TTSSynthesizer | None = None
        self._tts_busy = False   # sintez yoki ijro davom etayotganini bildiradi

        # --- Oldindan tayyorlash (pre-generation): "Boshlash" bosilgach,
        # har bir so'z uchun yordamchi audio FONDA, birma-bir oldindan
        # sintez qilinadi. Shunda 5-chi xatoga yetganda audio darhol (qayta
        # sintez qilinmasdan) ijro etiladi - vaqt tejaladi va tarmoqqa
        # bog'liqlik kamayadi. Agar biror so'z hali tayyor bo'lmasa
        # (masalan, matn juda uzun bo'lsa), _trigger_help() jonli sintezga
        # o'tadi (pastga qarang) - hech qachon ishlamay qolmaydi.
        self._help_audio_files: dict[int, str] = {}   # so'z indeksi -> tayyor fayl yo'li
        self._pregen_queue: list[int] = []
        self._pregen_synth: TTSSynthesizer | None = None
        self._pregen_epoch = 0   # har bir yangi pregen "avlodi" uchun oshadi (pastga qarang)

        self._net_timer = QTimer(self)
        self._net_timer.timeout.connect(self._check_internet)
        self._net_timer.start(5000)
        self._check_internet()

    # ------------------------------------------------------------------ #
    # Sozlash
    # ------------------------------------------------------------------ #
    @property
    def is_session_active(self) -> bool:
        return self._session_active

    def set_language(self, language_name: str):
        self.language = language_name

    def set_speed(self, speed_percent: int):
        """GUI'dagi tezlik slayderidan chaqiriladi (20% - 150%, 100% = standart)."""
        self.speed_percent = max(MIN_SPEED_PERCENT, min(MAX_SPEED_PERCENT, speed_percent))

    def set_tts_mode(self, mode: str):
        """GUI'dagi 'Ovoz manbai' tanlovidan chaqiriladi: 'online' yoki 'offline'."""
        if mode not in ("online", "offline"):
            return
        self.tts_mode = mode

        if mode == "offline":
            # Offline rejimda internetni tekshirishning hojati yo'q - fonda
            # doimiy ulanishga urinishni to'xtatamiz.
            self._net_timer.stop()
        else:
            self._net_timer.start(5000)
            self._check_internet()

        # Eski oldindan-tayyorlangan fayllar boshqa ovoz manbaida yaratilgan
        # bo'lishi mumkin - agar seans faol bo'lsa, ularni yangi manba bilan
        # qayta tayyorlaymiz.
        if self._session_active:
            self._start_pregeneration()

    def _current_rate_str(self) -> str:
        """Tanlangan tezlik foizini edge-tts'ning 'rate' formatiga o'giradi."""
        delta = self.speed_percent - 100
        return f"{delta:+d}%"

    def _current_wpm(self) -> int:
        """Tanlangan tezlik foizini espeak-ng'ning so'z/daqiqa (wpm) qiymatiga o'giradi."""
        wpm = int(ESPEAK_BASE_WPM * self.speed_percent / 100)
        return max(ESPEAK_MIN_WPM, min(ESPEAK_MAX_WPM, wpm))

    def _make_synthesizer(self, text: str, slow: bool):
        """
        Joriy tanlangan ovoz manbaiga (online/offline) qarab mos Synthesizer
        Thread'ini yaratadi. Ikkalasi ham bir xil signal interfeysiga ega
        (`synthesis_ready`/`error_occurred`), shuning uchun chaqiruvchi kod
        qaysi turi ekanidan qat'iy nazar bir xil ishlaydi.
        """
        lang_info = LANGUAGES[self.language]
        if self.tts_mode == "offline":
            pitch = OFFLINE_HELP_PITCH if slow else OFFLINE_NORMAL_PITCH
            return OfflineTTSSynthesizer(
                text, lang_info["espeak_voice"], wpm=self._current_wpm(), pitch=pitch, parent=self
            )

        pitch = TTS_PITCH if slow else "+0Hz"
        return TTSSynthesizer(
            text, lang_info["tts_voice"], rate=self._current_rate_str(), pitch=pitch, parent=self
        )

    def load_text(self, text: str):
        tokens = tokenize_text(text)
        self.display_tokens = [display for display, _clean in tokens]
        self.words = [clean for _display, clean in tokens]
        self.current_index = 0
        self.error_counts = {i: 0 for i in range(len(self.words))}
        # Eski matnga tegishli pregen (agar hali fonda ishlab turgan bo'lsa)
        # endi noto'g'ri indekslarga ega bo'lib qoladi - uni bekor qilamiz.
        self._cleanup_pregenerated_files()

    # ------------------------------------------------------------------ #
    # Dastlabki tinglash (SRS 3.4)
    # ------------------------------------------------------------------ #
    def start_pre_listening(self):
        if not self.words:
            self.status_message.emit("Avval matn kiriting.")
            return
        if self._session_active:
            # Mikrofon faol paytida butun matnni ovozli o'qish mikrofonga
            # "eshitilib", noto'g'ri aniqlanishlarga sabab bo'lishi mumkin edi.
            self.status_message.emit("Avval mashqni to'xtating, keyin tinglang.")
            return
        if self._tts_busy:
            # Sintez yoki ijro allaqachon davom etmoqda - qayta so'rov yubormaymiz
            # (bir nechta QMediaPlayer/ijroni bir vaqtda ochish beqarorlikka olib kelgan edi)
            return

        full_text = " ".join(self.display_tokens)

        self._tts_busy = True
        self.pre_listen_busy_changed.emit(True)
        self.status_message.emit("Matn tayyorlanmoqda...")
        print(f"[VoxTil] Dastlabki tinglash: sintez boshlandi ({self.tts_mode})")

        self._synth_worker = self._make_synthesizer(full_text, slow=False)
        self._synth_worker.synthesis_ready.connect(
            lambda path: self._start_playback(path, "pre_listen")
        )
        self._synth_worker.error_occurred.connect(self._on_synth_error)
        self._synth_worker.finished.connect(self._synth_worker.deleteLater)
        self._synth_worker.start()

    # ------------------------------------------------------------------ #
    # Asosiy mashq jarayoni (SRS 3.2, 3.3)
    # ------------------------------------------------------------------ #
    def start_session(self):
        if not self.words:
            self.status_message.emit("Avval matn kiriting.")
            return

        # MUHIM (topilgan xato): agar "Dastlabki tinglash" hali davom
        # etayotgan bo'lsa (ijro yoki hali sintez bosqichida) va shu payt
        # "Boshlash" bosilsa, audio to'xtamay davom etar edi - mikrofon esa
        # darhol faollashib, o'sha audioni "eshitib", uni xato ravishda
        # foydalanuvchining o'z ovozi deb hisoblardi (garchi foydalanuvchi
        # jim tursa ham). Shuning uchun mikrofonni yoqishdan oldin har
        # qanday faol ijroni darhol bekor qilamiz.
        #
        # `_session_active` ATAYLAB shu bekor qilishdan OLDIN True qilinadi:
        # bekor qilish `pre_listen_busy_changed` signalini yuboradi, va UI
        # o'sha signalni ushlaganda seans allaqachon faol deb bilishi kerak
        # - aks holda "Dastlabki tinglash" tugmasi bir lahzaga noto'g'ri
        # qayta yoqilib qolar edi.
        self._session_active = True
        self._cancel_active_playback()

        model_path = LANGUAGES[self.language]["vosk_model"]
        self.current_index = 0
        self.error_counts = {i: 0 for i in range(len(self.words))}
        self.word_status_changed.emit(0, "current")

        self.audio_worker = AudioWorker(model_path, parent=self)
        self.audio_worker.text_recognized.connect(self._on_text_recognized)
        self.audio_worker.error_occurred.connect(self.status_message.emit)
        self.audio_worker.start()
        self.status_message.emit("Mikrofon faol...")

        self._start_pregeneration()

    def stop_session(self):
        self._session_active = False
        if self.audio_worker:
            self.audio_worker.stop()
            self.audio_worker = None
        self._cleanup_pregenerated_files()
        self.status_message.emit("To'xtatildi.")

    def _on_text_recognized(self, text: str, is_final: bool):
        if not self._session_active or self.current_index >= len(self.words):
            return

        candidate_words = text.strip().split()
        if not candidate_words:
            return

        turkish = LANGUAGES[self.language].get("lang_code") == "tr"

        # Ravon/tez nutqda (ayniqsa qisqa so'zlar tez aytilganda) Vosk'ning
        # bitta yangilanishi bir nechta kutilayotgan so'zni birga qamrab
        # olishi mumkin (masalan "men maktabga" bitta partial'da chiqishi
        # mumkin, garchi ular ikkita alohida kutilayotgan so'z bo'lsa ham).
        # Shuning uchun faqat oxirgi so'z emas, oxirgi bir nechta so'z
        # tekshiriladi, va mos kelsa ketma-ket bir nechta so'z ilgari
        # surilishi mumkin.
        advanced = False
        while self.current_index < len(self.words):
            expected = self.words[self.current_index]
            lookback = candidate_words[-MATCH_LOOKBACK:]
            if any(is_match(expected, candidate, turkish=turkish) for candidate in lookback):
                self._advance_word()
                advanced = True
                continue
            break

        if advanced or not is_final or self.current_index >= len(self.words):
            return

        # Final (tugallangan) natija va baribir mos kelmadi - bu haqiqiy,
        # tugallangan noto'g'ri urinish hisoblanadi.
        expected = self.words[self.current_index]
        self.error_counts[self.current_index] += 1
        count = self.error_counts[self.current_index]
        print(f"[VoxTil] Xato #{count}/{ERROR_LIMIT}: kutilgan={expected!r}, eshitilgan={last_word(text)!r}")
        if count >= ERROR_LIMIT:
            self._trigger_help()
        else:
            self.status_message.emit(f'"{expected}" - xato {count}/{ERROR_LIMIT}')

    def _advance_word(self):
        self.word_status_changed.emit(self.current_index, "done")
        self.current_index += 1

        if self.audio_worker:
            self.audio_worker.reset_recognizer()

        if self.current_index >= len(self.words):
            self._finish_session()
        else:
            self.word_status_changed.emit(self.current_index, "current")

    def _trigger_help(self):
        if self._tts_busy:
            print("[VoxTil] Yordam so'raldi, lekin TTS band - o'tkazib yuborildi")
            return

        expected = self.words[self.current_index]

        if self.audio_worker:
            self.audio_worker.pause_listening()

        self._tts_busy = True
        self.status_message.emit(f'Yordam: "{expected}" so\'zi o\'qib berilmoqda...')

        pregenerated_path = self._help_audio_files.pop(self.current_index, None)
        if pregenerated_path and os.path.exists(pregenerated_path):
            print(f"[VoxTil] Oldindan tayyorlangan audio ishlatildi: {expected!r}")
            self._start_playback(pregenerated_path, "help")
            return

        print(f"[VoxTil] Oldindan tayyor emas - jonli sintez qilinmoqda ({self.tts_mode}): {expected!r}")
        self._synth_worker = self._make_synthesizer(expected, slow=True)
        self._synth_worker.synthesis_ready.connect(
            lambda path: self._start_playback(path, "help")
        )
        self._synth_worker.error_occurred.connect(self._on_synth_error)
        self._synth_worker.finished.connect(self._synth_worker.deleteLater)
        self._synth_worker.start()

    # ------------------------------------------------------------------ #
    # Audio ijrosi (har doim asosiy Thread'da, bitta umumiy player orqali)
    # ------------------------------------------------------------------ #
    def _start_playback(self, file_path: str, kind: str):
        if kind == "pre_listen" and self._session_active:
            # Sintez hali tugamasdan turib foydalanuvchi "Boshlash"ni bosgan
            # bo'lishi mumkin - bu audio endi kerak emas, ijro qilinmaydi
            # (aks holda mikrofon uni "eshitib" qolar edi).
            try:
                os.remove(file_path)
            except OSError:
                pass
            self._tts_busy = False
            return

        self._playback_kind = kind
        self._playback_file = file_path
        self._media_player.setSource(QUrl.fromLocalFile(file_path))
        self._media_player.play()
        # Bitta so'z uchun 20s, butun matn uchun so'zlar soniga qarab (kamida 20s)
        # - agar shu vaqt ichida "tugadi" signali kelmasa, majburan tozalaymiz.
        timeout_ms = 20000 if kind == "help" else max(20000, len(self.words) * 1500)
        self._playback_watchdog.start(timeout_ms)
        print(f"[VoxTil] Ijro boshlandi ({kind}): {file_path}")

    def _on_media_status_changed(self, status):
        finished_states = (
            QMediaPlayer.MediaStatus.EndOfMedia,
            QMediaPlayer.MediaStatus.InvalidMedia,
        )
        if status not in finished_states or self._playback_kind is None:
            return
        print(f"[VoxTil] Ijro tugadi, holat: {status}")
        self._finish_playback()

    def _on_media_error(self, error, error_string):
        if self._playback_kind is None:
            return
        print(f"[VoxTil] Audio ijrosida xato: {error_string}")
        self.status_message.emit(f"Audio ijrosida xato: {error_string}")
        self._finish_playback()

    def _on_playback_timeout(self):
        if self._playback_kind is None:
            return
        print("[VoxTil] OGOHLANTIRISH: audio ijrosi kutilgan vaqtda tugamadi, majburan tozalanmoqda")
        self.status_message.emit("Audio ijrosida kutilmagan kechikish - davom etilmoqda.")
        self._finish_playback()

    def _cancel_active_playback(self):
        """
        Hozir ijro etilayotgan yoki hali sintez qilinayotgan har qanday
        audioni (masalan, "Dastlabki tinglash") darhol bekor qiladi.
        `start_session()` mikrofonni yoqishdan oldin shuni chaqiradi.
        """
        self._playback_watchdog.stop()
        self._media_player.stop()
        if self._playback_file:
            try:
                os.remove(self._playback_file)
            except OSError:
                pass
        self._playback_kind = None
        self._playback_file = None
        self._tts_busy = False
        self.pre_listen_busy_changed.emit(False)

    def _finish_playback(self):
        """Ijro tugagach (normal, xato yoki timeout tufayli) umumiy tozalash."""
        kind = self._playback_kind
        old_file = self._playback_file
        self._playback_kind = None
        self._playback_file = None
        self._playback_watchdog.stop()
        self._media_player.stop()

        if old_file:
            try:
                os.remove(old_file)
            except OSError:
                pass

        self._tts_busy = False

        if kind == "help":
            self._on_help_finished()
        elif kind == "pre_listen":
            self.pre_listen_busy_changed.emit(False)
            self.status_message.emit("Tayyor. 'Boshlash' tugmasini bosing.")

    # ------------------------------------------------------------------ #
    # Yordamchi audiolarni oldindan tayyorlash (fonda, "Boshlash"dan keyin)
    #
    # MUHIM (topilgan xato): agar `load_text()` yangi matn bilan chaqirilsa
    # (yoki tezlik/til/ovoz manbai o'zgarib pregen qayta boshlansa) aynan
    # ESKI pregen zanjiri hali fonda ishlab turgan (masalan, tarmoq javobini
    # kutayotgan) bo'lsa, uning natijasi keyinchalik ESKI indeks bilan YANGI
    # (ehtimol qisqaroq) `self.words` ro'yxatiga yozilishga urinib,
    # `IndexError` bilan dasturni qulatishi mumkin edi - bu real holatda oson
    # yuz beradi (masalan, foydalanuvchi matnni tez tugatib, pregen hali
    # tugamasdan turib darhol yangi matn yuklasa). Shuning uchun har bir
    # pregen "avlodi" (epoch) raqamlanadi - eskirgan avloddan kelgan har
    # qanday natija sezilmasdan tashlab yuboriladi.
    # ------------------------------------------------------------------ #
    def _start_pregeneration(self):
        self._cleanup_pregenerated_files()
        epoch = self._pregen_epoch
        self._pregen_queue = list(range(len(self.words)))
        self._pregen_next(epoch)

    def _pregen_next(self, epoch: int):
        if epoch != self._pregen_epoch:
            # Eskirgan avlod - joriy holatga umuman tegmaymiz (yangi avlod
            # allaqachon o'zining _pregen_synth'ini boshlagan bo'lishi mumkin).
            return

        if not self._pregen_queue:
            self._pregen_synth = None
            return

        index = self._pregen_queue.pop(0)
        word = self.words[index]

        self._pregen_synth = self._make_synthesizer(word, slow=True)
        self._pregen_synth.synthesis_ready.connect(
            lambda path, idx=index, ep=epoch: self._on_pregen_ready(ep, idx, path)
        )
        self._pregen_synth.error_occurred.connect(
            lambda message, idx=index, ep=epoch: self._on_pregen_error(ep, idx, message)
        )
        self._pregen_synth.finished.connect(self._pregen_synth.deleteLater)
        self._pregen_synth.start()

    def _on_pregen_ready(self, epoch: int, index: int, path: str):
        if epoch != self._pregen_epoch:
            # Eskirgan natija - endi kerak emas, faylni tozalab, e'tibor bermaymiz.
            try:
                os.remove(path)
            except OSError:
                pass
            return

        self._help_audio_files[index] = path
        # Qo'shimcha xavfsizlik: keyingisini boshlashdan oldin eski Thread
        # haqiqatan to'xtaganini tasdiqlaymiz (odatda darhol qaytadi, chunki
        # bu signal `run()` deyarli tugagach yuborilgan edi).
        if self._pregen_synth is not None:
            self._pregen_synth.wait(1000)
        self._pregen_next(epoch)

    def _on_pregen_error(self, epoch: int, index: int, message: str):
        if epoch != self._pregen_epoch:
            return
        print(f"[VoxTil] So'z #{index} uchun oldindan tayyorlash muvaffaqiyatsiz: {message}")
        if self._pregen_synth is not None:
            self._pregen_synth.wait(1000)
        self._pregen_next(epoch)

    def _cleanup_pregenerated_files(self):
        for path in self._help_audio_files.values():
            try:
                os.remove(path)
            except OSError:
                pass
        self._help_audio_files = {}
        self._pregen_queue = []
        # Avlod raqamini oshiramiz - hali fonda ishlab turgan (eski avlodga
        # tegishli) har qanday pregen natijasi endi e'tiborsiz qoldiriladi.
        self._pregen_epoch += 1

    def _on_synth_error(self, message: str):
        self._tts_busy = False
        if not self._session_active:
            # pre_listen_busy_changed FAQAT "Dastlabki tinglash" tugmasi
            # uchun mo'ljallangan; seans faol bo'lsa (demak xato aslida
            # yordam-audiosidan kelgan), bu signalni yubormaymiz - aks holda
            # "Dastlabki tinglash" tugmasi seans davomida noto'g'ri qayta
            # yoqilib qolar edi.
            self.pre_listen_busy_changed.emit(False)
        self.status_message.emit(message)
        print(f"[VoxTil] Sintez xatosi: {message}")
        if self.audio_worker:
            self.audio_worker.resume_listening()

    def _on_help_finished(self):
        self.error_counts[self.current_index] = 0
        if self.audio_worker:
            self.audio_worker.resume_listening()
        self.status_message.emit("Mikrofon faol...")

    def _finish_session(self):
        self._session_active = False
        if self.audio_worker:
            self.audio_worker.stop()
            self.audio_worker = None
        self._cleanup_pregenerated_files()

        # MUHIM (topilgan xato): matnda bir xil so'z bir necha marta
        # uchrashi mumkin (masalan "mushuk ... mushuk"). So'z matnini kalit
        # sifatida ishlatgan oddiy lug'at bunday holda oldingi holatni
        # keyingisi bilan "yozib qo'yar edi" - masalan birinchi "mushuk"da
        # 3 marta, ikkinchisida 1 marta xato bo'lsa, faqat oxirgisi (1)
        # ko'rsatilib, umumiy rasm noto'g'ri chiqardi. Endi bir xil so'zning
        # barcha holatlaridagi xatolar QO'SHIB hisoblanadi.
        struggled: dict[str, int] = {}
        for i, count in self.error_counts.items():
            if count > 0:
                word = self.words[i]
                struggled[word] = struggled.get(word, 0) + count

        stats = {
            "total_words": len(self.words),
            "struggled_words": struggled,
        }
        self.status_message.emit("Tabriklaymiz! Matn tugadi.")
        self.session_finished.emit(stats)

    def _check_internet(self):
        self.internet_status_changed.emit(is_internet_available())

    def shutdown(self):
        """
        Dastur oynasi yopilayotganda chaqirilishi kerak (MainWindow.closeEvent).

        Agar foydalanuvchi TTS sintezi yoki ijrosi hali davom etayotganda
        oynani yopib yuborsa, fon Thread'lari (TTSSynthesizer/AudioWorker)
        hali to'liq to'xtamagan holda dastur bilan birga yo'q qilinishi
        mumkin edi - bu xuddi shu "QThread: Destroyed while thread is still
        running" xatosiga olib kelardi (v1.5 da boshqa holat uchun
        tuzatilgan edi, lekin dastur yopilishi alohida holat). Shuning uchun
        yopishdan oldin barcha fon Thread'lari xavfsiz tugashini kutamiz.
        """
        self._session_active = False
        self._net_timer.stop()
        self._playback_watchdog.stop()

        if self.audio_worker:
            self.audio_worker.stop()
            self.audio_worker = None

        for worker in (self._synth_worker, self._pregen_synth):
            if worker is None:
                continue
            try:
                if worker.isRunning():
                    worker.wait(3000)
            except RuntimeError:
                # `finished -> deleteLater()` orqali C++ obyekt allaqachon
                # tozalangan bo'lishi mumkin (worker o'z ishini tugatib
                # ulgurgan) - bu holda Python'dagi eski havola endi
                # "muallaqlashgan" (dangling) hisoblanadi va unga har
                # qanday murojaat shu xatoni beradi. Bemalol o'tkazib
                # yuboramiz - bu safe, chunki thread allaqachon tugagan.
                pass

        self._cleanup_pregenerated_files()
