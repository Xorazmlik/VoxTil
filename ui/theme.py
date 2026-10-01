"""
VoxTil uchun dizayn tizimi (2-bosqich): ranglar, shriftlar va QSS
uslub varag'i. Bu fayl butun dasturning vizual "shaxsiyatini" bir joyda
saqlaydi, shunda kelajakda uslubni o'zgartirish uchun boshqa fayllarga
tegish shart bo'lmaydi.

Yo'nalish: iliq, qog'ozsimon (light) mavzu + chuqur teal/o'rmon-yashil urg'u.
Bu til o'rganish uchun tinch, diqqatni chalg'itmaydigan "o'qish xonasi"
kayfiyatini beradi - foydalanuvchi asosiy e'tibori matnga qaratilishi kerak,
interfeys esa uni bezovta qilmasligi lozim.

So'z holatlari uchun rang tanlovi ataylab uchta aniq bosqichni ifodalaydi:
  kulrang (hali navbat kelmadi) -> amber (hozir shu so'z) -> yashil (bajarildi)
Bu tabiiy "o'sish yo'li" hikoyasini beradi va uchala holatni bir-biridan
osongina farqlash imkonini beradi.
"""

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QFont, QIcon, QPainter, QPixmap

# --- Ranglar (hex) ---
BG_WINDOW = "#FAF6EF"       # asosiy oyna foni - iliq qog'oz rangi
BG_SURFACE = "#FFFFFF"      # matn ko'rsatiladigan asosiy karta foni
BG_HEADER = "#F3EEE4"       # header/footer uchun biroz to'qroq iliq fon
BORDER = "#E3DBCB"          # yupqa, iliq ajratuvchi chiziq

INK = "#2B2A28"             # asosiy matn rangi (yumshoq deyarli qora)
INK_MUTED = "#8B8378"       # ikkinchi darajali matn (hali navbat kelmagan so'zlar)

ACCENT = "#2F6F5E"          # chuqur teal/o'rmon-yashil - asosiy urg'u rangi
ACCENT_HOVER = "#26594B"
ACCENT_PRESSED = "#1E463B"
ACCENT_LIGHT = "#E3EFEA"    # och teal fon (slayder yo'lagi va h.k. uchun)

CURRENT_BG = "#FBEACD"      # joriy so'z uchun issiq amber fon
CURRENT_TEXT = "#7A4E00"

DONE_BG = "#DCEEE3"         # to'g'ri o'qilgan so'z uchun yumshoq yashil fon
DONE_TEXT = "#1F5C3F"

ERROR_TEXT = "#A85D3B"      # xato/ogohlantirish matni uchun bosiq to'q sariq

DISABLED_BG = "#EDE7DA"
DISABLED_TEXT = "#B7AE9E"

SUCCESS_DOT = "#3F8F5F"
WARNING_DOT = "#B5573C"

# --- Shriftlar ---
# DejaVu/Noto oilalari lotin-kengaytirilgan belgilarni (o'zbekcha va turkcha
# harflar: o', g', ş, ğ, ı va h.k.) to'liq qo'llab-quvvatlaydi, shuning uchun
# faqat "chiroyli" emas, balki amaliy tanlov ham hisoblanadi.
FONT_UI = '"Noto Sans", "DejaVu Sans", "Segoe UI", Arial, sans-serif'
FONT_READING = '"Noto Serif", "DejaVu Serif", Georgia, serif'


def build_stylesheet() -> str:
    """Butun dastur uchun QSS uslub varag'ini qaytaradi."""
    return f"""
    QMainWindow, QDialog {{
        background-color: {BG_WINDOW};
    }}

    QWidget {{
        font-family: {FONT_UI};
        color: {INK};
        font-size: 14px;
    }}

    /* --- Header/Footer paneli --- */
    QFrame#headerPanel, QFrame#footerPanel {{
        background-color: {BG_HEADER};
        border: none;
    }}
    QFrame#headerPanel {{
        border-bottom: 1px solid {BORDER};
    }}
    QFrame#dividerLine {{
        color: {BORDER};
        background-color: {BORDER};
        max-width: 1px;
        min-width: 1px;
    }}

    /* --- Tugmalar --- */
    QPushButton {{
        background-color: {BG_SURFACE};
        color: {INK};
        border: 1px solid {BORDER};
        border-radius: 7px;
        padding: 7px 16px;
        font-weight: 500;
    }}
    QPushButton:hover {{
        border-color: {ACCENT};
        color: {ACCENT};
    }}
    QPushButton:pressed {{
        background-color: {ACCENT_LIGHT};
    }}
    QPushButton:disabled {{
        background-color: {DISABLED_BG};
        color: {DISABLED_TEXT};
        border-color: {DISABLED_BG};
    }}

    QPushButton#primaryButton {{
        background-color: {ACCENT};
        color: white;
        border: 1px solid {ACCENT};
        font-weight: 600;
    }}
    QPushButton#primaryButton:hover {{
        background-color: {ACCENT_HOVER};
        color: white;
        border-color: {ACCENT_HOVER};
    }}
    QPushButton#primaryButton:pressed {{
        background-color: {ACCENT_PRESSED};
    }}
    QPushButton#primaryButton:disabled {{
        background-color: {DISABLED_BG};
        color: {DISABLED_TEXT};
        border-color: {DISABLED_BG};
    }}

    /* --- Combo, Slider --- */
    QComboBox {{
        background-color: {BG_SURFACE};
        border: 1px solid {BORDER};
        border-radius: 7px;
        padding: 6px 10px;
        min-width: 100px;
    }}
    QComboBox:hover {{
        border-color: {ACCENT};
    }}
    QComboBox QAbstractItemView {{
        background-color: {BG_SURFACE};
        border: 1px solid {BORDER};
        selection-background-color: {ACCENT_LIGHT};
        selection-color: {INK};
        outline: none;
    }}

    QSlider::groove:horizontal {{
        height: 5px;
        background: {ACCENT_LIGHT};
        border-radius: 2px;
    }}
    QSlider::sub-page:horizontal {{
        background: {ACCENT};
        border-radius: 2px;
    }}
    QSlider::handle:horizontal {{
        background: {ACCENT};
        width: 15px;
        height: 15px;
        margin: -5px 0;
        border-radius: 7px;
    }}
    QSlider::handle:horizontal:hover {{
        background: {ACCENT_HOVER};
    }}

    /* --- Matn ko'rsatish kartasi --- */
    QTextBrowser#readingCard {{
        background-color: {BG_SURFACE};
        border: 1px solid {BORDER};
        border-radius: 12px;
        padding: 28px;
        font-family: {FONT_READING};
        font-size: 27px;
        selection-background-color: {ACCENT_LIGHT};
    }}

    /* --- Matn kiritish dialogi --- */
    QPlainTextEdit {{
        background-color: {BG_SURFACE};
        border: 1px solid {BORDER};
        border-radius: 8px;
        padding: 10px;
        font-family: {FONT_READING};
        font-size: 16px;
    }}
    QPlainTextEdit:focus {{
        border-color: {ACCENT};
    }}

    /* --- Status qatori --- */
    QStatusBar {{
        background-color: {BG_HEADER};
        border-top: 1px solid {BORDER};
        color: {INK_MUTED};
    }}
    QStatusBar::item {{
        border: none;
    }}

    QProgressBar {{
        background-color: {ACCENT_LIGHT};
        border: none;
        border-radius: 5px;
        height: 10px;
        text-align: center;
    }}
    QProgressBar::chunk {{
        background-color: {ACCENT};
        border-radius: 5px;
    }}

    QLabel#mutedLabel {{
        color: {INK_MUTED};
    }}
    QLabel#dialogHeading {{
        font-size: 20px;
        font-weight: 700;
        color: {INK};
    }}
    QLabel#dialogSubheading {{
        color: {INK_MUTED};
        font-size: 14px;
    }}

    /* --- Ro'yxat (masalan, natijalar oynasidagi qiynalgan so'zlar) --- */
    QListWidget {{
        background-color: {BG_SURFACE};
        border: 1px solid {BORDER};
        border-radius: 8px;
        padding: 4px;
        outline: none;
    }}
    QListWidget::item {{
        padding: 8px 10px;
        border-radius: 6px;
        color: {INK};
    }}
    QListWidget::item:selected {{
        background-color: {ACCENT_LIGHT};
        color: {INK};
    }}
    QListWidget::item:hover {{
        background-color: {BG_HEADER};
    }}
    """


def make_app_icon() -> QIcon:
    """
    Dastur uchun oddiy, faylsiz belgi (icon) yaratadi: teal doira ichida
    "LK" harflari. Tashqi rasm fayllariga bog'liq bo'lmaslik uchun to'g'ridan-
    to'g'ri QPainter bilan chiziladi.
    """
    size = 128
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.GlobalColor.transparent)

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)

    painter.setBrush(QColor(ACCENT))
    painter.setPen(Qt.PenStyle.NoPen)
    painter.drawEllipse(4, 4, size - 8, size - 8)

    painter.setPen(QColor("white"))
    font = QFont(FONT_UI.split(",")[0].strip('"'))
    font.setBold(True)
    font.setPointSize(44)
    painter.setFont(font)
    painter.drawText(pixmap.rect(), int(Qt.AlignmentFlag.AlignCenter), "LK")

    painter.end()
    return QIcon(pixmap)
