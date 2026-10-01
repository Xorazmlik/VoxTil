"""
Talaffuz qilingan so'zni kutilayotgan so'z bilan solishtirish (SRS 3.2).
"""

from thefuzz import fuzz

from config import MATCH_THRESHOLD, SHORT_WORD_LENGTH, SHORT_WORD_THRESHOLD
from utils.text_processor import normalize_word


def is_match(
    expected_word: str,
    recognized_text: str,
    threshold: int | None = None,
    turkish: bool = False,
) -> bool:
    """
    Kutilayotgan so'z aniqlangan so'z/matn bilan mos kelishini tekshiradi.

    MUHIM (qisqa so'zlar uchun maxsus qoida): oddiy `partial_ratio` uzun
    so'zlar uchun yaxshi ishlaydi (Vosk natijasidagi ortiqcha harflarga
    chidamli), lekin 2-3 harfli so'zlar ("bu", "va", "u") uchun xavfli -
    ular tasodifan UMUMAN ALOQASI BO'LMAGAN uzunroq so'zlar ichida harfma-
    harf uchrab qolishi mumkin (masalan "bu" so'zi "kabul" ichida bor,
    natijada partial_ratio 100% qaytaradi!). Shuning uchun qisqa so'zlar
    uchun to'liq (`ratio`) solishtiruv ishlatiladi - bu umumiy uzunlik
    farqini ham hisobga oladi va bunday soxta mosliklarni oldini oladi.
    Chegara ham shu holat uchun biroz pastroq qo'yiladi, chunki qisqa
    so'zda hatto bitta harf farqi ham foizni keskin pasaytiradi.
    """
    if not expected_word or not recognized_text:
        return False

    expected = normalize_word(expected_word, turkish=turkish)
    recognized = normalize_word(recognized_text, turkish=turkish)

    if len(expected) <= SHORT_WORD_LENGTH:
        score = fuzz.ratio(expected, recognized)
        effective_threshold = threshold if threshold is not None else SHORT_WORD_THRESHOLD
    else:
        score = fuzz.partial_ratio(expected, recognized)
        effective_threshold = threshold if threshold is not None else MATCH_THRESHOLD

    return score >= effective_threshold


def last_word(text: str) -> str:
    """Matndagi oxirgi so'zni qaytaradi (Vosk partial natijasini tez tekshirish uchun)."""
    words = text.strip().split()
    return words[-1] if words else ""


def last_words(text: str, n: int) -> list[str]:
    """
    Matndagi oxirgi N ta so'zni qaytaradi. Ravon/tez nutqda Vosk'ning bitta
    yangilanishi bir nechta kutilayotgan so'zni birga qamrab olishi mumkin
    (ayniqsa qisqa so'zlar tez aytilganda), shuning uchun faqat oxirgi
    so'zga emas, oxirgi bir nechtasiga qarash kerak bo'ladi.
    """
    words = text.strip().split()
    return words[-n:] if words else []
