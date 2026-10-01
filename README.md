# VoxTil — 1-bosqich (MVP)

Real vaqtda talaffuzni tinglab, matn bilan solishtiradigan va xato ko'p bo'lsa
ovozli yordam beradigan desktop mashq dasturi.

Bu — **1-bosqich**: SRS hujjatida ko'rsatilgan barcha funksional talablar
ishlaydigan holatda, lekin dizayni hali sodda ("minimum ishlovchi mahsulot").
Dizaynni chiroylashtirish va ishlashni siqiqlashtirish **2-bosqich**da amalga
oshiriladi.

## Loyiha tuzilmasi

```
VoxTil/
├── main.py                 # Ishga tushirish nuqtasi
├── config.py               # Barcha sozlamalar (threshold, xato limiti, tillar...)
├── controller.py           # Asosiy mantiq (so'zlar, xatolar, TTS boshqaruvi)
├── requirements.txt
├── ui/
│   ├── main_window.py      # Oyna: header/body/footer, dialoglar
│   └── theme.py            # Dizayn tizimi: ranglar, shriftlar, QSS, ikonka
├── workers/
│   ├── audio_worker.py     # Mikrofon + Vosk (STT) — alohida Thread
│   ├── tts_worker.py       # ONLAYN TTS: edge-tts + ijro — alohida Thread
│   └── offline_tts_worker.py # OFFLINE TTS: espeak-ng — alohida Thread
├── utils/
│   ├── text_processor.py   # Matnni so'zlarga ajratish
│   ├── matcher.py          # Fuzzy matching (thefuzz)
│   └── network.py           # Internetni tekshirish
├── models/                 # Vosk modellari shu yerga joylashtiriladi (bo'sh)
└── temp_audio/             # Vaqtinchalik TTS audio fayllari (avtomatik)
```

## 1. O'rnatish

### 1.1. Tizim kutubxonalari (PyAudio uchun shart)

**Linux (Ubuntu/Debian):**
```bash
sudo apt update
sudo apt install portaudio19-dev python3-pyaudio
```

**Windows:**
Agar `pip install pyaudio` xato bersa, oldindan tayyorlangan `.whl` fayldan
o'rnating (masalan, `pipwin install pyaudio` yoki
[gohlke saytidan](https://www.lfd.uci.edu/~gohlke/pythonlibs/) mos versiyani
yuklab oling).

### 1.2. Offline ovoz uchun espeak-ng (ixtiyoriy, lekin tavsiya etiladi)

Dastur ikki xil ovoz manbaida ishlay oladi: **Onlayn** (edge-tts, internet
talab qiladi, ovoz tabiiyroq) va **Offline** (espeak-ng, internetga umuman
muhtoj emas, ovoz mexanikroq lekin talaffuzi aniq). Ular orasida dastur
ichida, "Ovoz:" tanlovi orqali istalgan vaqtda almashish mumkin.

Offline rejim ishlashi uchun espeak-ng alohida o'rnatilishi kerak (bu pip
paketi emas, alohida dastur):

```bash
# Linux (Ubuntu/Debian):
sudo apt install espeak-ng
```

Windows uchun: https://github.com/espeak-ng/espeak-ng/releases sahifasidan
o'rnatuvchini yuklab oling.

Agar espeak-ng o'rnatilmagan bo'lsa, dastur ishlayveradi - shunchaki
"Offline" rejimni tanlaganingizda tushunarli xato xabari chiqadi va Onlayn
rejimga qaytish tavsiya etiladi.

### 1.3. Python kutubxonalari

```bash
git clone https://github.com/Xorazmlik/VoxTil.git
cd VoxTil
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 1.4. Vosk modellarini yuklab olish (oflayn nutqni aniqlash uchun)

Har bir til uchun kichik Vosk modelini https://alphacephei.com/vosk/models
sahifasidan yuklab oling, arxivdan chiqaring va `models/` papkasiga
joylashtiring. Papka nomi `config.py` dagi `LANGUAGES` lug'atidagi
`vosk_model` yo'liga **aynan mos kelishi kerak**:

```
models/vosk-model-small-tr-0.3/     <- Turkcha
models/vosk-model-small-uz-0.22/    <- O'zbekcha
models/vosk-model-small-en-us-0.15/ <- Inglizcha
```

Agar boshqa til/model ishlatmoqchi bo'lsangiz, `config.py` faylidagi
`LANGUAGES` lug'atiga yangi qator qo'shing.

> Faqat kerakli tillar uchun modelni yuklab olsangiz kifoya — masalan, faqat
> turkcha bilan ishlaydigan bo'lsangiz, boshqa ikkitasi shart emas, lekin til
> tanlash menyusida ular ishlamaydi.

## 2. Ishga tushirish

```bash
python main.py
```

**Diqqat:** dastlabki tinglash va xato-yordam (TTS) funksiyalari uchun
internet aloqasi kerak (`edge-tts` Microsoft xizmatidan foydalanadi).
Nutqni aniqlash (Vosk) esa to'liq oflayn ishlaydi.

## 3. Qanday ishlaydi (qisqacha)

1. **"Matn yuklash"** tugmasi orqali mashq matnini kiriting.
2. Xohlasangiz, **"Dastlabki tinglash"** orqali matnni to'liq eshiting.
3. **"Boshlash"**ni bosing — mikrofon faollashadi, birinchi so'z sariq fonda
   ko'rsatiladi.
4. So'zni talaffuz qiling. To'g'ri chiqsa (≥ 80% o'xshashlik), so'z yashil
   rangga o'tadi va navbat keyingisiga o'tadi.
5. Bir so'zda 5 marta xato qilsangiz, dastur mikrofonni to'xtatib, so'zni
   sekin va aniq o'qib beradi, so'ng davom etadi.
6. Matn tugaganda, qaysi so'zlarda ko'p qiynalganingiz haqida statistika
   chiqadi.

## 4. Ma'lum cheklovlar

- So'z chegaralarini aniqlash Vosk'ning partial/final natijalariga asoslangan
  taxminiy yondashuv; ba'zi tillarda/mikrofonlarda nozik sozlash kerak
  bo'lishi mumkin (kerak bo'lsa `config.py` dagi `MATCH_THRESHOLD` ni
  o'zgartiring).
- Bitta seansda faqat bitta til modeli ishlatiladi (seansni qayta
  boshlaganda tilni almashtirish mumkin).

## 5. v1.2 da tuzatilgan xatoliklar va yangi imkoniyat

- **"Failed to process waveform" / Aborted xatosi tuzatildi:** Bu xato
  Vosk'ning `KaldiRecognizer` obyekti Thread-xavfsiz emasligidan kelib
  chiqqan edi — asosiy (GUI) Thread `Reset()`ni to'g'ridan-to'g'ri
  chaqirayotganda, fon Thread aynan shu obyekt bilan `AcceptWaveform()`
  orqali band bo'lishi mumkin edi (poyga holati / race condition). Endi
  `Reset()` faqat bayroq orqali so'raladi va uni **faqat** `AudioWorker`ning
  o'zi, o'z Thread'i ichida bajaradi. Bu simulyatsiya qilingan yuqori
  chastotali sinovda tasdiqlandi (200 marta ketma-ket pause/resume/reset —
  hech qanday konflikt yo'q).
- **Ovoz tezligini tanlash qo'shildi:** Header qismida "Tezlik" slayderi
  paydo bo'ldi (20% dan 150% gacha, standart holat — 100%). Bu tezlik endi
  ham "Dastlabki tinglash", ham xato-yordam audiosiga qo'llaniladi. Slayderni
  suring — masalan, 50% qilib qo'ysangiz, barcha ovozli o'qishlar sekinroq
  bo'ladi.

## 6. v1.3 da tuzatilgan asosiy xato: yordam ishga tushmasligi

- **Sabab topildi:** `is_internet_available()` funksiyasi DNS portiga
  (8.8.8.8:53) ulanishni tekshirar edi. Ko'p tarmoqlar/routerlar bu portni
  bloklaydi — garchi internetning o'zi normal ishlasa ham. Natijada, 5-chi
  xatodan keyin dastur "internet yo'q" deb **noto'g'ri xulosaga kelib**,
  ovozli yordamni sukut bilan o'tkazib yuborar va xato hisoblagichini jim-
  jimgina nolga tushirar edi — tashqaridan qaraganda "xatoni aniqlaydi, lekin
  hech qachon o'qib bermaydi" bo'lib ko'rinar edi.
- **Tuzatildi:** endi TTS oldindan "internet bormi" deb so'ramaydi — to'g'ridan-
  to'g'ri sintez qilishga urinadi. Agar bu haqiqatan muvaffaqiyatsiz bo'lsa
  (internet yo'q, server javob bermasa), aniq xato xabari chiqadi va so'z
  hisoblagichi **saqlanib qoladi** (keyingi xato urinishida yana sinaydi),
  hech qachon jimgina yo'qolib ketmaydi.
- **Qo'shimcha himoya:** agar audio qurilmasi muammosi tufayli ijro "osilib
  qolsa", 20 soniyadan keyin tizim avtomatik o'zini tozalab, ishni davom
  ettiradi (soqchi-timer / watchdog).
- **Jonli status:** endi har bir xato urinishida pastki qatorda
  `"so'z" - xato N/5` ko'rinishida hisoblagich ko'rsatiladi, shunda nechta
  urinish qolganini aniq ko'rasiz. Terminalda ham `[VoxTil]` prefiksli
  qatorlar orqali batafsil diagnostika chiqadi — agar yana muammo bo'lsa, shu
  qatorlarni yuboring.

## 7. v1.4: partial xatolar muammosi va oldindan-tayyorlash

- **"Bir marta xato qilsam o'zi 1 dan 5gacha sanaydi" muammosi tuzatildi:**
  sabab — Vosk so'zni bosqichma-bosqich taniydi (masalan "salom" so'zi uchun
  avval "s", keyin "sa", "sal"... deb chiqaradi). Bu oraliq (partial)
  natijalar hali TUGALLANMAGAN, shuning uchun ular hali to'liq so'zga mos
  kelmasligi tabiiy holat — lekin avvalgi versiyada bu ham xato deb
  hisoblanar edi! Natijada bitta (hatto TO'G'RI aytilgan) urinish ichida
  hisoblagich soxta ravishda tezda 5gacha yetib qolishi mumkin edi. Endi:
  partial natijalar faqat TEZ ijobiy moslikni aniqlash uchun ishlatiladi
  (so'z to'g'ri aytilsa, darhol yashilga o'tadi — 500ms talabi saqlanadi),
  xato hisoblagichi esa faqat Vosk **tugallangan** (final) natija chiqarib,
  u baribir mos kelmasa oshiriladi — bu haqiqatan bitta to'liq, noto'g'ri
  chiqqan urinishni bildiradi.
- **Oldindan tayyorlash (pre-generation) qo'shildi:** "Boshlash" bosilgach,
  matndagi har bir so'z uchun yordamchi audio fonda, birma-bir oldindan
  sintez qilib qo'yiladi (foydalanuvchi hali o'sha so'zga yetib kelmagan
  bo'lsa ham). 5-chi xatoga yetilganda, agar audio allaqachon tayyor bo'lsa,
  u **qayta sintez qilinmasdan, darhol** ijro etiladi — bu ham vaqtni
  tejaydi, ham tarmoqqa bog'liqlikni kamaytiradi. Agar biror so'z hali
  tayyor bo'lmagan bo'lsa (masalan, juda uzun matn yoki sekin internet),
  tizim avtomatik ravishda jonli sintezga o'tadi — hech qachon butunlay
  ishlamay qolmaydi.

## 8. v1.5: "QThread: Destroyed while thread is still running" tuzatildi

- **Sabab:** yordamchi audio yaratuvchi `QThread` obyektlari (`TTSSynthesizer`)
  hech qanday Qt "ota" (parent) obyektiga bog'lanmagan edi. Ularning umri
  faqat oddiy Python o'zgaruvchisi orqali saqlanardi. Oldindan-tayyorlash
  (pre-generation) fonda ko'plab so'zlarni tez-tez ketma-ket sintez qilar
  ekan, har safar navbatdagi so'z uchun yangi obyekt o'sha o'zgaruvchiga
  qayta yozilar edi — agar shu payt eski obyekt hali Qt darajasida to'liq
  "to'xtadi" deb belgilanmagan bo'lsa (garchi `run()` allaqachon tugagan
  bo'lsa ham), Python uni erta o'chirib yuborishi mumkin edi. Bu klassik
  PyQt xatosi — `QThread: Destroyed while thread is still running` — va
  dasturning butunlay qulashiga (`Aborted`) sabab bo'lgan.
- **Tuzatildi:** endi barcha `TTSSynthesizer`/`AudioWorker` obyektlari
  `parent=controller` bilan yaratiladi (bu ularni C++ darajasida tirik
  saqlaydi) va `finished` signali `deleteLater()`ga ulanadi (bu ularni FAQAT
  thread haqiqatan to'xtagandan keyin xavfsiz tozalaydi). Bundan tashqari,
  oldindan-tayyorlash zanjirida keyingi so'zga o'tishdan oldin eski
  Thread'ning to'liq tugaganini `wait()` bilan qo'shimcha tasdiqlaymiz.
  50 ta so'zli matn bilan butun zanjirni sinovdan o'tkazdim — hech qanday
  ogohlantirish yoki qulash yo'q.

## 9. v2.0 — 2-bosqich: dizayn va professional ko'rinish

1-bosqichda dastur to'liq ishlaydigan (funksional) holatga keltirilgan edi.
2-bosqichda esa uni "tayyor mahsulot" ko'rinishiga olib chiqildi:

- **Yagona dizayn tizimi (`ui/theme.py`):** barcha ranglar, shriftlar va
  uslublar bitta faylda to'plangan. Yo'nalish — iliq, qog'ozsimon (light)
  fon + chuqur teal/o'rmon-yashil urg'u rangi, xotirjam va diqqatni
  matnning o'ziga qaratadigan "o'qish xonasi" kayfiyati bilan.
- **Uch bosqichli vizual hikoya:** so'zlar endi kulrang (navbat kelmagan) ->
  amber-rangli chip (hozir shu so'z) -> yumshoq yashil chip (bajarildi)
  tartibida ko'rinadi — matn bo'ylab tabiiy "o'sish yo'li" hissi beradi.
- **Guruhlangan boshqaruv paneli:** tugmalar mantiqiy guruhlarga (matn
  boshqaruvi / seans boshqaruvi / til va tezlik) ajratilib, ular orasiga
  nozik ajratuvchi chiziqlar qo'yildi.
- **Progress ko'rsatkichi:** pastki qatorda "X / Y so'z" - nechta so'z
  bajarilgani doim ko'rinib turadi.
- **Yangi natijalar oynasi:** oddiy tizim xabarnomasi o'rniga, dizaynga mos
  maxsus oyna - sarlavha, qisqacha statistika va qiynalgan so'zlar ro'yxati
  chiroyli ko'rinishda.
- **Dastur belgisi (ikonka):** oyna sarlavhasi va vazifalar panelida
  ko'rinadigan, tashqi fayllarga bog'liq bo'lmagan, dasturiy chizilgan
  belgi (teal doira ichida "LK").
- **Unicode-mos shriftlar:** o'zbekcha/turkcha maxsus harflar (o', g', ş,
  ğ, ı) uchun to'liq qo'llab-quvvatlovchi shrift oilalari tanlandi.

Barcha o'zgarishlar offscreen rejimda skrinshot olib tekshirildi - QSS
xatoliklarisiz, barcha dialoglar to'g'ri qurilishi tasdiqlandi.

## 10. v2.1 — offline (internetsiz) ovoz rejimi

Foydalanuvchi so'roviga ko'ra, dastur endi ikki xil ovoz manbaida ishlay
oladi:

- **Onlayn** (`workers/tts_worker.py`, edge-tts) — tabiiyroq, sifatli ovoz,
  internet talab qiladi.
- **Offline** (`workers/offline_tts_worker.py`, espeak-ng) — internetga
  umuman muhtoj emas, ovoz mexanikroq (formant sintez), lekin talaffuzi
  aniq. Turkcha, o'zbekcha va inglizcha uchun rasman qo'llab-quvvatlanadi.

Header qatoridagi **"Ovoz:"** tanlovi orqali ular orasida istalgan vaqtda
almashish mumkin — hatto mashq davomida ham (bunday holda oldindan
tayyorlangan yordamchi audiolar yangi manba bilan avtomatik qayta
tayyorlanadi). Offline rejim tanlanganda, fonda internetni tekshirish ham
to'xtatiladi — dastur haqiqatan hech qanday tarmoq so'rovi yubormaydi.

**Eslatma:** Vosk (nutqni aniqlash) bu o'zgarishga aloqasi yo'q — u
boshidanoq 100% oflayn ishlagan.

Ikkala rejimda ham (jumladan oldindan-tayyorlash va 5-xato-yordam oqimi bilan
birga) haqiqiy audio generatsiya qilib sinovdan o'tkazildi.

## 11. v2.2 — qisqa so'zlar muammosi va boshqa aniqlangan nuqsonlar

Foydalanuvchi 2-3 harfli so'zlarni ("bu", "va", "u") aniqlashda xatolik
borligini payqadi. Chuqur tekshiruv natijasida bu bitta emas, balki
bir-biriga bog'liq **to'rtta** muammo ekani aniqlandi:

1. **Soxta substring moslik (asosiy sabab):** oddiy fuzzy-matching (`partial_ratio`)
   qisqa so'zlarni tekshirganda, ular tasodifan UMUMAN ALOQASI BO'LMAGAN
   uzunroq so'zlar ICHIDA harfma-harf topilib qolar edi - masalan "bu" so'zi
   "kabul" ichida, "u" esa "kuni" ichida bor, va bu 100% mos deb hisoblanardi!
   Tuzatildi: endi qisqa so'zlar (3 harf va undan qisqa) uchun to'liq (`ratio`)
   solishtiruv ishlatiladi - bu umumiy uzunlik farqini ham hisobga oladi.
2. **Ravon nutqda so'zlar birlashib ketishi:** qisqa so'zlar tez aytilgani
   uchun, Vosk ba'zan ularni keyingi so'z bilan BIRGA, bitta partial
   natijada chiqarishi mumkin edi (masalan "men" o'rniga to'g'ridan-to'g'ri
   "men maktabga"). Tizim faqat OXIRGI so'zni tekshirgani uchun, qisqa so'z
   "yo'qolib" qolardi. Tuzatildi: endi oxirgi so'z emas, oxirgi bir nechta
   so'z tekshiriladi va mos kelsa, ketma-ket bir nechta so'z bir yo'la
   ilgari surilishi mumkin.
3. **Apostrof variantlari:** o'zbekcha "o'"/"g'" harfi turli manbalarda
   har xil Unicode belgi bilan yozilishi mumkin (to'g'ri tirnoq, qiya
   tirnoq, maxsus belgi). Matn va Vosk natijasi har xil variantdan
   foydalansa, to'g'ri talaffuz ham mos kelmay qolardi - va bu farq
   qisqa so'zlarda katta foizli ta'sir qiladi. Tuzatildi: barcha variantlar
   solishtirishdan oldin bitta belgiga tenglashtiriladi.
4. **Turkcha "İ" harfi:** standart Python katta-kichik harf almashtirish
   turkcha "İ" ni nostandart ikki belgili shaklga aylantiradi, Vosk esa
   oddiy "i" kutadi. Tuzatildi: turkcha tanlanganda maxsus qoida qo'llaniladi.

Bulardan tashqari, testlash davomida yana bir mustaqil xato topildi va
tuzatildi: agar foydalanuvchi TTS ishlab turganda dastur oynasini yopib
yuborsa, fon Thread hali tugamagan holda majburan o'chirilib, "QThread:
Destroyed while thread is still running" xatosi bilan qulashi mumkin edi
(xuddi v1.5 dagi kabi, lekin bu safar "dastur yopilishi" holati uchun).
Endi oyna yopilishida barcha fon Thread'lar xavfsiz tugashini kutadi.

Barcha tuzatishlar real (mock qilinmagan) misollar bilan sinovdan
 o'tkazildi: soxta substring rad etilishi, apostrof variantlari, turkcha
 harf, ravon nutqda so'z birlashishi va TTS ishlab turganda yopish stsenariysi.

## 12. v2.3 — chuqur testlashda topilgan qo'shimcha nuqsonlar

Foydalanuvchi ruxsati bilan kodni yanada chuqur, mustaqil testlashda yana
**to'qqizta** real muammo topildi va tuzatildi:

**Matnni tokenlashtirishda:**
1. Faqat tinish belgilaridan iborat "so'z" (masalan, yolg'iz `'''`) haqiqiy
   amaliyot so'zi sifatida hisoblanar edi - endi kamida bitta harf/raqam
   bo'lmasa, token butunlay e'tiborsiz qoldiriladi.
2. Probelsiz, ketma-ket tinish belgilari bilan yopishgan so'zlar (masalan
   `salom,,,,dunyo`) ajratilmay, bitta ulkan, hech qachon mos kelmaydigan
   "so'z" bo'lib qolardi - endi istalgan tinish belgisi (apostrof va oddiy
   defisdan tashqari) so'z chegarasi sifatida hisoblanadi, probel bo'lsa
   ham, bo'lmasa ham.

**Pre-generation zanjirida (jiddiy, real qulash xatosi):**
3. Agar foydalanuvchi bir matnni tez tugatib (yoki "Boshlash"ni bosib),
   pre-generation hali fonda ishlab turganida YANGI matn yuklasa, eski
   zanjirning natijasi yangi (qisqaroq) so'zlar ro'yxatiga eski indeks bilan
   yozilishga urinib, **`IndexError` bilan dasturni butunlay qulatishi**
   mumkin edi. Bu ehtimol eng jiddiy topilma edi - real foydalanishda oson
   yuz berishi mumkin.
4. Xuddi shu vaziyatda, hatto qulash yuz bermasa ham, ESKI so'zga tegishli
   tayyor audio fayl YANGI so'zning joyiga (bir xil indeks bo'yicha)
   yozilib, keyinchalik butunlay boshqa so'z uchun noto'g'ri audio ijro
   etilishi mumkin edi.

   Ikkalasi ham "avlod" (epoch) mexanizmi bilan tuzatildi: har bir pre-
   generation urinishi raqamlanadi, va eskirgan avloddan kelgan har qanday
   natija endi sezilmasdan tashlab yuboriladi.

**Seans boshqaruvida:**
5. Mashq seansi (mikrofon) faol paytida **tilni almashtirish** mumkin edi -
   bu esa nutqni aniqlash (eski til modeli) va ovozli yordam (yangi til)
   o'rtasida nomuvofiqlikka olib kelardi. Endi til tanlovi seans davomida
   bloklanadi.
6. Mashq seansi faol paytida **"Dastlabki tinglash"** tugmasi ham bosilishi
   mumkin edi - bu esa butun matnni ovozli o'qib, mikrofonga "eshittirib",
   noto'g'ri aniqlanishlarga sabab bo'lishi mumkin edi. Endi seans davomida
   bloklanadi (ham tugma, ham controller darajasida).
7. Agar seans faol paytida yordamchi audio (help) sinteziga xato tushsa,
   bu xato noto'g'ri ravishda "Dastlabki tinglash" tugmasini qayta yoqib
   yuborar edi (ikkala funksiya bitta signalni ulashgani sabab). Tuzatildi.

**Statistikada:**
8. Agar matnda bir xil so'z bir necha marta uchrasa (masalan "mushuk ...
   mushuk"), natijalar oynasidagi statistika so'zni kalit sifatida
   ishlatgani uchun oldingi holatni keyingisi bilan **"yozib qo'yar"** edi -
   masalan birinchi holatda 3 marta, ikkinchisida 1 marta xato bo'lsa,
   faqat oxirgisi ko'rsatilardi. Endi bir xil so'zning barcha holatlaridagi
   xatolar qo'shib hisoblanadi.

**Dizaynda:**
9. Natijalar oynasidagi ro'yxat (`QListWidget`) uchun maxsus uslub yo'q edi,
   shuning uchun u standart (mos kelmaydigan) ko'rinishda chiqishi mumkin
   edi. Endi umumiy dizayn tizimiga mos.

Barcha to'qqiz tuzatish alohida, real (mock qilinmagan yoki maqsadli mock
bilan) sinovlar orqali tasdiqlandi - jumladan aynan qulashga sabab bo'lgan
stsenariyning o'zi qayta ishga tushirilib, endi xavfsiz ishlashi ko'rsatildi.

## 13. v2.4 — "Dastlabki tinglash" + "Boshlash" ziddiyati tuzatildi

Foydalanuvchi topgan xato: "Dastlabki tinglash" audiosi hali o'qib
berilayotganda "Boshlash" bosilsa, audio to'xtamay davom etar edi.
Natijada mikrofon darhol faollashib, o'sha (hali davom etayotgan) audioni
"eshitib", uni xato ravishda foydalanuvchining o'z ovozi deb hisoblardi -
foydalanuvchi butunlay jim tursa ham.

**Sabab:** `start_session()` mikrofonni yoqishdan oldin faol audio ijrosini
(yoki hali tugamagan sintezni) tekshirmas va to'xtatmas edi.

**Tuzatildi:** endi `start_session()` mikrofonni yoqishdan oldin har qanday
faol "Dastlabki tinglash" audiosini (ijro bosqichida bo'lsa - darhol
to'xtatib; hali sintez bosqichida bo'lsa - tayyor bo'lganda ijro etilishini
bekor qilib) tozalaydi. Ikkala holat ham (ijro paytida va sintez paytida
"Boshlash" bosilishi) alohida sinovdan o'tkazildi.

Bu tuzatish davomida yana ikkita nozik, bog'liq xato ham topildi va
tuzatildi:
- Signal tartibi muammosi: bekor qilish signali ba'zan "Dastlabki tinglash"
  tugmasini seans davomida bir lahzaga noto'g'ri qayta yoqib yuborar edi
  (endi tugma holati bir vaqtning o'zida ham "band", ham "seans faol"
  holatini hisobga oladi).
- `shutdown()` allaqachon `deleteLater()` orqali tozalangan Thread
  obyektiga murojaat qilsa, `RuntimeError` bilan yiqilishi mumkin edi -
  endi bunday holat xavfsiz o'tkazib yuboriladi.

## 14. Keyingi bosqichlar

- **3-bosqich (ixtiyoriy):** foydalanish davomida aniqlangan xatoliklarni
  tuzatish va foydalanuvchi tajribasini yanada silliqlashtirish.
