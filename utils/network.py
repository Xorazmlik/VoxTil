"""
Internetga ulanishni tekshirish uchun yordamchi funksiya (SRS 4-band).

Eslatma: bu funksiya faqat Footer'dagi "Internet: ulangan/yo'q" ko'rsatkichi
uchun ma'lumot beradi (kosmetik). TTS ishlashi endi bu tekshiruvga BOG'LIQ
EMAS — chunki DNS portiga (53) ulanishni tekshirish ba'zi tarmoqlarda
(masalan, 53-port bloklangan, lekin internet aslida ishlaydigan tarmoqlarda)
noto'g'ri "yo'q" natija berib, ovozli yordamni asossiz o'tkazib yuborishga
sabab bo'lgan edi. Endi TTS to'g'ridan-to'g'ri sintez qilishga urinadi va
faqat haqiqatan muvaffaqiyatsiz bo'lsa xato ko'rsatadi (workers/tts_worker.py).
"""

import socket

# HTTPS (443) porti deyarli barcha tarmoqlarda ochiq bo'ladi (DNS porti 53
# dan farqli o'laroq), shuning uchun kosmetik ko'rsatkich uchun ham shu
# ishlatiladi. Bir nechta xost sinaladi - biri ishlamasa, ikkinchisi sinaladi.
_CHECK_HOSTS = [("8.8.8.8", 443), ("1.1.1.1", 443)]


def is_internet_available(timeout: float = 2.0) -> bool:
    """Internet mavjudligini taxminan tekshiradi (faqat kosmetik ko'rsatkich uchun)."""
    for host, port in _CHECK_HOSTS:
        try:
            socket.setdefaulttimeout(timeout)
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((host, port))
            s.close()
            return True
        except OSError:
            continue
    return False
