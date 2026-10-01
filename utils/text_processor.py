"""
Matnni tokenlarga ajratish funksiyalari (SRS 7-band, 2-qadam).

Har bir token uchun ikkita shakl saqlanadi:
  - "asl" (display) shakl - tinish belgilari (vergul, nuqta va h.k.) bilan,
    ekranda tabiiy ko'rinishda ko'rsatish uchun.
  - "toza" (match) shakl - faqat harf/raqamlardan iborat, talaffuzni
    solishtirish uchun (tinish belgilari moslikka xalaqit bermasligi kerak).
"""

import re

# Token boshi/oxiridagi so'z bo'lmagan belgilarni (vergul, nuqta, tirnoq...)
# kesib olish uchun. Apostrof (' va ') so'z ichida qoladi (masalan, "ko'k"),
# xuddi shu tarzda oddiy defis ("-") ham so'z ichida (leading/trailing bo'lmasa) qoladi.
_TRIM_RE = re.compile(r"^[^\w'’]+|[^\w'’]+$", re.UNICODE)

# So'z ICHIDA saqlanadigan yagona-belgili tinish belgilari: apostrof
# variantlari (o'zbekcha "o'"/"g'" uchun) va oddiy defis (qo'shma so'zlar
# uchun, masalan "ob-havo", "otam-buvam"). Boshqa har qanday tinish belgisi
# (vergul, nuqta, em/en-dash va h.k.) so'z chegarasi hisoblanadi va probel
# bo'lmasa ham so'zlarni ajratib turadi.
_KEEP_INTERNAL = set("'’‘ʻʼ`´-")

# Turli manbalarda "o'"/"g'" kabi harflar uchun ishlatiladigan apostrofga
# o'xshash belgilar - hammasi bitta belgiga tenglashtiriladi (pastga qarang).
_APOSTROPHE_VARIANTS = "\u2018\u2019\u02bb\u02bc\u0060\u00b4"
_APOSTROPHE_CANONICAL = "'"


def _split_internal_punctuation(token: str) -> list[str]:
    """
    Probelsiz ulangan so'zlarni (masalan "Bu—dastur" yoki "salom,,,,dunyo")
    tinish belgilari bo'yicha ajratadi, belgini oldingi qismga bog'lab
    qoldiradi (ko'rsatishda tabiiy ko'rinishi uchun, masalan "Bu—" va
    "dastur", yoki "salom," va "dunyo"). Apostrof va oddiy defis so'z
    ichida saqlanadi (_KEEP_INTERNAL), boshqa hamma narsa ajratuvchi
    hisoblanadi - garchi orasida probel bo'lmasa ham.
    """
    parts = []
    current = ""
    for ch in token:
        current += ch
        if not (ch.isalnum() or ch in _KEEP_INTERNAL):
            parts.append(current)
            current = ""
    if current:
        parts.append(current)
    return parts if parts else [token]


def _has_letter_or_digit(text: str) -> bool:
    """Matnda kamida bitta harf/raqam borligini tekshiradi (faqat apostrof/
    defisdan iborat "so'z" - masalan yolg'iz \"'''\" - so'z hisoblanmasligi uchun)."""
    return any(ch.isalnum() for ch in text)


def tokenize_text(text: str) -> list[tuple[str, str]]:
    """
    Matnni bo'sh joy bo'yicha tokenlarga ajratadi va har biri uchun
    (asl_token, toza_soz) juftligini qaytaradi. Toza so'zi bo'sh chiqadigan
    yoki hech qanday harf/raqam saqlamaydigan tokenlar (masalan, yolg'iz
    "-", "..." yoki "'''") natijaga qo'shilmaydi, lekin asl matndagi boshqa
    barcha tinish belgilari ko'rsatish uchun saqlanadi.
    """
    if not text:
        return []

    result: list[tuple[str, str]] = []
    for raw in text.split():
        for piece in _split_internal_punctuation(raw):
            clean = _TRIM_RE.sub("", piece)
            if clean and _has_letter_or_digit(clean):
                result.append((piece, clean))
    return result


def normalize_word(word: str, turkish: bool = False) -> str:
    """
    Solishtirish uchun so'zni kichik harflarga o'tkazadi va bo'shliqlarni
    olib tashlaydi. Bundan tashqari ikkita nozik, lekin real muammoni
    hal qiladi:

    1. Apostrof variantlari: o'zbekcha (va boshqa) matnlarda "o'" harfi
       turli manbalarda har xil Unicode belgi bilan yozilishi mumkin -
       oddiy to'g'ri tirnoq ('), o'ng qiya tirnoq (\u2019) yoki maxsus
       "modifier letter" belgisi (\u02bb). Agar matn va Vosk'ning chiqishi
       har xil variantdan foydalansa, aks holda to'g'ri talaffuz ham mos
       kelmay qolar edi. Shuning uchun barcha variantlar bitta belgiga
       tenglashtiriladi.
    2. Turkcha katta-kichik harf: standart Python `.lower()` turkcha "İ"
       harfini nostandart, ikki belgili "i\u0307" ga aylantiradi (Unicode
       standart qoidasi bo'yicha), Vosk esa oddiy "i" harfini kutadi. Bu
       ayniqsa "İ" bilan boshlanadigan so'zlarni har doim xato deb
       ko'rsatishiga sabab bo'lar edi. `turkish=True` bo'lsa, bu maxsus
       hisobga olinadi.
    """
    text = word.strip()

    if turkish:
        text = text.replace("İ", "i").replace("I", "ı")

    text = text.lower()

    for variant in _APOSTROPHE_VARIANTS:
        text = text.replace(variant, _APOSTROPHE_CANONICAL)

    return text
