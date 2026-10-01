"""
VoxTil - Global konfiguratsiya va sozlamalar.

Barcha "sehrli sonlar" va sozlanadigan qiymatlar shu faylda to'plangan,
shunda ularni kodning ichiga kirmasdan osongina o'zgartirish mumkin.
"""

import os

# --- Fuzzy matching (talaffuzni tekshirish) sozlamalari ---
MATCH_THRESHOLD = 80          # So'z to'g'ri deb hisoblanishi uchun minimal o'xshashlik foizi (SRS 3.2)
ERROR_LIMIT = 5               # Nechta xatodan keyin TTS yordami ishga tushishi (SRS 3.3)

# Juda qisqa (masalan, 2-3 harfli: "bu", "va", "u") so'zlarni oddiy "partial"
# moslik bilan solishtirish xato edi: ular tasodifan uzunroq, umuman
# aloqasi bo'lmagan so'zlar ICHIDA harfma-harf uchrab qolib, soxta ravishda
# 100% mos deb hisoblanishi mumkin ("bu" so'zi "kabul" ichida uchraydi).
# Shu uzunlikdagi va undan qisqa so'zlar uchun boshqacha (to'liq, ratio
# asosidagi) solishtiruv qo'llaniladi - bunda chegara biroz pastroq, chunki
# qisqa so'zda hatto bitta harf farqi ham foizni keskin pasaytiradi.
SHORT_WORD_LENGTH = 3
SHORT_WORD_THRESHOLD = 65

# Ravon/tez nutqda bir nechta kutilayotgan so'z (ayniqsa qisqalari) Vosk'ning
# bitta partial/final yangilanishida birga chiqishi mumkin. Shuning uchun
# faqat oxirgi so'z emas, oxirgi shuncha so'z tekshiriladi.
MATCH_LOOKBACK = 3

# --- TTS (edge-tts, ONLAYN) sozlamalari ---
TTS_PITCH = "-5Hz"            # Yordamchi audio uchun biroz yumshoqroq ohang, xotirjamlik uchun

# Ovoz tezligini GUI orqali tanlash (foizda, 100% = standart tezlik).
# Bu qiymat edge-tts'ning "rate" parametriga (masalan, "-30%", "+20%")
# aylantiriladi: rate = tanlangan_tezlik - 100.
MIN_SPEED_PERCENT = 20
MAX_SPEED_PERCENT = 150
DEFAULT_SPEED_PERCENT = 100

# --- TTS (espeak-ng, OFFLINE) sozlamalari ---
# espeak-ng alohida dastur sifatida o'rnatilishi kerak (pip orqali emas):
#     Linux:   sudo apt install espeak-ng
#     Windows: https://github.com/espeak-ng/espeak-ng/releases
# 100% tezlikka mos so'z/daqiqa qiymati (espeak-ng standarti ~175 dan
# birmuncha sekinroq - o'quv maqsadida aniqroq talaffuz uchun).
ESPEAK_BASE_WPM = 150
ESPEAK_MIN_WPM = 60
ESPEAK_MAX_WPM = 400
OFFLINE_NORMAL_PITCH = 50     # espeak-ng standart ohang (0-99 oralig'ida)
OFFLINE_HELP_PITCH = 42       # xato-yordam uchun biroz pastroq/yumshoqroq ohang

# Dastur ishga tushganda qaysi ovoz manbai tanlangan bo'ladi: "online" yoki "offline"
DEFAULT_TTS_MODE = "online"

# --- Audio (PyAudio + Vosk) sozlamalari ---
AUDIO_SAMPLE_RATE = 16000
AUDIO_CHUNK_SIZE = 4000
AUDIO_CHANNELS = 1

# --- Fayl yo'llari ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODELS_DIR = os.path.join(BASE_DIR, "models")
TEMP_AUDIO_DIR = os.path.join(BASE_DIR, "temp_audio")

os.makedirs(TEMP_AUDIO_DIR, exist_ok=True)

# --- Til sozlamalari ---
# Har bir til uchun: Vosk modeli papkasi (models/ ichiga yuklab olinishi kerak),
# edge-tts ONLAYN ovoz nomi va espeak-ng OFFLINE til kodi.
# Onlayn ovozlar ro'yxati uchun terminalda:  edge-tts --list-voices
# Offline (espeak-ng) tillar ro'yxati uchun: espeak-ng --voices
LANGUAGES = {
    "Turkcha (tr)": {
        "vosk_model": os.path.join(MODELS_DIR, "vosk-model-small-tr-0.3"),
        "tts_voice": "tr-TR-AhmetNeural",
        "espeak_voice": "tr",
        "lang_code": "tr",
    },
    "O'zbekcha (uz)": {
        "vosk_model": os.path.join(MODELS_DIR, "vosk-model-small-uz-0.22"),
        "tts_voice": "uz-UZ-SardorNeural",
        "espeak_voice": "uz",
        "lang_code": "uz",
    },
    "Inglizcha (en)": {
        "vosk_model": os.path.join(MODELS_DIR, "vosk-model-small-en-us-0.15"),
        "tts_voice": "en-US-GuyNeural",
        "espeak_voice": "en-us",
        "lang_code": "en",
    },
}

DEFAULT_LANGUAGE = "Turkcha (tr)"
