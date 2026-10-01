"""
MainWindow - VoxTil uchun asosiy oyna (SRS 6-band: UI Layout).

2-bosqich: professional ko'rinish. Vizual tizim ui/theme.py da saqlanadi;
bu fayl faqat komponentlar joylashuvi va ularning mantig'i bilan shug'ullanadi.
"""

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QComboBox,
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QSlider,
    QStatusBar,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)

from config import DEFAULT_SPEED_PERCENT, LANGUAGES, MAX_SPEED_PERCENT, MIN_SPEED_PERCENT
from controller import VoxTilController
from ui.theme import (
    CURRENT_BG,
    CURRENT_TEXT,
    DONE_BG,
    DONE_TEXT,
    INK_MUTED,
    SUCCESS_DOT,
    WARNING_DOT,
    make_app_icon,
)


def _divider() -> QFrame:
    """Header/footer ichida guruhlarni ajratuvchi yupqa vertikal chiziq."""
    line = QFrame()
    line.setObjectName("dividerLine")
    line.setFrameShape(QFrame.Shape.VLine)
    return line


class LoadTextDialog(QDialog):
    """Foydalanuvchi mashq matnini kiritishi uchun dialog oyna."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Matn yuklash")
        self.resize(540, 340)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(12)

        heading = QLabel("Mashq matnini kiriting")
        heading.setObjectName("dialogHeading")
        layout.addWidget(heading)

        subheading = QLabel("Bu matn talaffuz mashqi uchun so'z-so'z ko'rsatiladi.")
        subheading.setObjectName("dialogSubheading")
        layout.addWidget(subheading)

        self.text_edit = QPlainTextEdit()
        self.text_edit.setPlaceholderText("Masalan: Salom, bugun ob-havo juda yaxshi...")
        layout.addWidget(self.text_edit)

        button_row = QHBoxLayout()
        button_row.addStretch()
        cancel_btn = QPushButton("Bekor qilish")
        cancel_btn.clicked.connect(self.reject)
        save_btn = QPushButton("Saqlash")
        save_btn.setObjectName("primaryButton")
        save_btn.clicked.connect(self.accept)
        button_row.addWidget(cancel_btn)
        button_row.addWidget(save_btn)
        layout.addLayout(button_row)

    def get_text(self) -> str:
        return self.text_edit.toPlainText()


class ResultsDialog(QDialog):
    """Mashq yakunlangach ko'rsatiladigan natijalar oynasi (SRS 7-band, 7-qadam)."""

    def __init__(self, stats: dict, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Natija")
        self.resize(440, 380)

        total = stats.get("total_words", 0)
        struggled: dict = stats.get("struggled_words", {})
        clean_count = total - len(struggled)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 28, 28, 28)
        layout.setSpacing(10)

        heading = QLabel("Tabriklaymiz!")
        heading.setObjectName("dialogHeading")
        layout.addWidget(heading)

        summary = QLabel(f"{total} so'zdan {clean_count} tasi birinchi urinishda to'g'ri chiqdi.")
        summary.setObjectName("dialogSubheading")
        summary.setWordWrap(True)
        layout.addWidget(summary)

        if struggled:
            list_label = QLabel("Ko'proq mashq qilish tavsiya etiladigan so'zlar:")
            list_label.setObjectName("mutedLabel")
            layout.addWidget(list_label)

            word_list = QListWidget()
            word_list.setFocusPolicy(Qt.FocusPolicy.NoFocus)
            for word, count in struggled.items():
                item = QListWidgetItem(f"{word}  —  {count} marta qiynalindi")
                word_list.addItem(item)
            layout.addWidget(word_list)
        else:
            layout.addStretch()

        close_btn = QPushButton("Yopish")
        close_btn.setObjectName("primaryButton")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("VoxTil")
        self.setWindowIcon(make_app_icon())
        self.resize(1100, 680)
        self.setMinimumSize(1060, 520)

        self.controller = VoxTilController(self)
        self._word_html_states: list[str] = []

        self._build_ui()
        self._connect_signals()

    # ------------------------------------------------------------------ #
    # UI qurish
    # ------------------------------------------------------------------ #
    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root_layout = QVBoxLayout(central)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        root_layout.addWidget(self._build_header())

        body_wrapper = QWidget()
        body_layout = QVBoxLayout(body_wrapper)
        body_layout.setContentsMargins(20, 20, 20, 20)
        self.text_view = QTextBrowser()
        self.text_view.setObjectName("readingCard")
        self.text_view.setReadOnly(True)
        body_layout.addWidget(self.text_view)
        root_layout.addWidget(body_wrapper, stretch=1)

        self._build_footer()

    def _build_header(self) -> QFrame:
        panel = QFrame()
        panel.setObjectName("headerPanel")
        layout = QHBoxLayout(panel)
        layout.setContentsMargins(18, 14, 18, 14)
        layout.setSpacing(8)

        self.load_text_btn = QPushButton("Matn yuklash")
        self.pre_listen_btn = QPushButton("Dastlabki tinglash")
        layout.addWidget(self.load_text_btn)
        layout.addWidget(self.pre_listen_btn)

        layout.addWidget(_divider())

        self.start_btn = QPushButton("Boshlash")
        self.start_btn.setObjectName("primaryButton")
        self.stop_btn = QPushButton("To'xtatish")
        self.stop_btn.setEnabled(False)
        layout.addWidget(self.start_btn)
        layout.addWidget(self.stop_btn)

        layout.addStretch()

        self.language_combo = QComboBox()
        self.language_combo.addItems(list(LANGUAGES.keys()))
        self.language_combo.setToolTip("Mashq tili")
        layout.addWidget(self.language_combo)

        layout.addWidget(_divider())

        self.speed_slider = QSlider(Qt.Orientation.Horizontal)
        self.speed_slider.setMinimum(MIN_SPEED_PERCENT)
        self.speed_slider.setMaximum(MAX_SPEED_PERCENT)
        self.speed_slider.setValue(DEFAULT_SPEED_PERCENT)
        self.speed_slider.setFixedWidth(90)
        self.speed_slider.setToolTip("Ovoz tezligi")
        layout.addWidget(self.speed_slider)
        self.speed_value_label = QLabel(f"{DEFAULT_SPEED_PERCENT}%")
        self.speed_value_label.setObjectName("mutedLabel")
        self.speed_value_label.setFixedWidth(36)
        layout.addWidget(self.speed_value_label)

        layout.addWidget(_divider())

        self.tts_mode_combo = QComboBox()
        self.tts_mode_combo.addItems(["Onlayn (sifatli)", "Offline (internetsiz)"])
        self.tts_mode_combo.setToolTip(
            "Ovoz manbai\n"
            "Onlayn: edge-tts, tabiiyroq ovoz, internet talab qiladi.\n"
            "Offline: espeak-ng, internetga muhtoj emas, ovoz mexanikroq."
        )
        layout.addWidget(self.tts_mode_combo)

        return panel

    def _build_footer(self):
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Matn kutilmoqda...")

        self.progress_label = QLabel("")
        self.progress_label.setObjectName("mutedLabel")
        self.status_bar.addPermanentWidget(self.progress_label)

        self.status_bar.addPermanentWidget(_divider())

        self.internet_label = QLabel("● tekshirilmoqda...")
        self.status_bar.addPermanentWidget(self.internet_label)

    def _connect_signals(self):
        self.load_text_btn.clicked.connect(self._on_load_text)
        self.pre_listen_btn.clicked.connect(self.controller.start_pre_listening)
        self.start_btn.clicked.connect(self._on_start)
        self.stop_btn.clicked.connect(self._on_stop)
        self.language_combo.currentTextChanged.connect(self.controller.set_language)
        self.speed_slider.valueChanged.connect(self._on_speed_changed)
        self.tts_mode_combo.currentIndexChanged.connect(self._on_tts_mode_changed)

        self.controller.word_status_changed.connect(self._on_word_status_changed)
        self.controller.status_message.connect(self.status_bar.showMessage)
        self.controller.session_finished.connect(self._on_session_finished)
        self.controller.internet_status_changed.connect(self._on_internet_status_changed)
        self.controller.pre_listen_busy_changed.connect(self._on_pre_listen_busy_changed)

    # ------------------------------------------------------------------ #
    # Amallar
    # ------------------------------------------------------------------ #
    def _on_load_text(self):
        dialog = LoadTextDialog(self)
        if dialog.exec():
            text = dialog.get_text().strip()
            if not text:
                return
            self.controller.load_text(text)
            self._word_html_states = ["pending"] * len(self.controller.words)
            self._render_text()
            self._update_progress_label()
            self.status_bar.showMessage("Matn yuklandi. 'Boshlash' tugmasini bosing.")

    def _on_start(self):
        if not self.controller.words:
            QMessageBox.information(self, "Diqqat", "Avval matn yuklang.")
            return
        self._word_html_states = ["pending"] * len(self.controller.words)
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.load_text_btn.setEnabled(False)
        # Til seans boshida tanlangan Vosk modeliga bog'lab qo'yiladi - seans
        # davomida almashtirilsa, nutqni aniqlash (eski til) va ovozli yordam
        # (yangi til) o'rtasida nomuvofiqlik yuzaga kelardi.
        self.language_combo.setEnabled(False)
        self.pre_listen_btn.setEnabled(False)
        self.controller.start_session()
        self._update_progress_label()

    def _on_stop(self):
        self.controller.stop_session()
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.load_text_btn.setEnabled(True)
        self.language_combo.setEnabled(True)
        self.pre_listen_btn.setEnabled(True)
        self.progress_label.setText("")

    def _on_word_status_changed(self, index: int, state: str):
        if 0 <= index < len(self._word_html_states):
            self._word_html_states[index] = state
            self._render_text()
            self._update_progress_label()

    def _on_session_finished(self, stats: dict):
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.load_text_btn.setEnabled(True)
        self.language_combo.setEnabled(True)
        self.pre_listen_btn.setEnabled(True)
        ResultsDialog(stats, self).exec()

    def _on_internet_status_changed(self, connected: bool):
        dot_color = SUCCESS_DOT if connected else WARNING_DOT
        text = "ulangan" if connected else "yo'q (onlayn ovoz ishlamasligi mumkin)"
        self.internet_label.setText(f"● {text}")
        self.internet_label.setStyleSheet(f"color: {dot_color};")

    def _on_speed_changed(self, value: int):
        self.speed_value_label.setText(f"{value}%")
        self.controller.set_speed(value)

    def _on_tts_mode_changed(self, index: int):
        mode = "offline" if index == 1 else "online"
        self.controller.set_tts_mode(mode)
        if mode == "offline":
            self.internet_label.setText("● Offline rejim")
            self.internet_label.setStyleSheet(f"color: {INK_MUTED};")

    def _on_pre_listen_busy_changed(self, busy: bool):
        """
        `pre_listen_busy_changed` signalidan chaqiriladi. Faqat "band"
        holatiga emas, balki seans faolligiga ham qaraydi - aks holda,
        masalan, "Boshlash" bosilganda ("Dastlabki tinglash" hali davom
        etayotgan bo'lsa) bekor qilish signali tugmani seans davomida
        noto'g'ri qayta yoqib yuborishi mumkin edi.
        """
        self.pre_listen_btn.setEnabled(not busy and not self.controller.is_session_active)

    def _update_progress_label(self):
        total = len(self.controller.words)
        if total == 0:
            self.progress_label.setText("")
            return
        done_count = sum(1 for s in self._word_html_states if s == "done")
        self.progress_label.setText(f"{done_count} / {total} so'z")

    def closeEvent(self, event):
        """
        Oyna yopilayotganda fon Thread'lari (TTS sintezi, mikrofon)
        xavfsiz tugashini kutadi - aks holda ular hali ishlab turgan
        holda majburan o'chirilib, dastur qulashiga sabab bo'lishi mumkin.
        """
        self.controller.shutdown()
        super().closeEvent(event)

    # ------------------------------------------------------------------ #
    # Matnni render qilish (so'zlarni holatiga qarab ranglash)
    # ------------------------------------------------------------------ #
    def _render_text(self):
        colors = {
            "pending": INK_MUTED,
            "current": CURRENT_TEXT,
            "done": DONE_TEXT,
        }
        backgrounds = {
            "current": f"background-color:{CURRENT_BG};",
            "done": f"background-color:{DONE_BG};",
        }
        weights = {
            "current": "font-weight:600;",
        }

        spans = []
        for word, state in zip(self.controller.display_tokens, self._word_html_states):
            color = colors.get(state, INK_MUTED)
            bg = backgrounds.get(state, "")
            weight = weights.get(state, "")
            style = f"color:{color};{bg}{weight}padding:3px 5px;"
            spans.append(f'<span style="{style}">{word}</span>')

        self.text_view.setHtml(" ".join(spans))
