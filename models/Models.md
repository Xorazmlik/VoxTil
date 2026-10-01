# Models Directory

Bu papka ishlatiladigan ASR/Vosk modellari uchun saqlash nuqtasi hisoblanadi.

## Qoidalar

- Barcha model fayllari shu `models/` papkada saqlanishi kerak.
- Dastur `config.py` ichidagi `LANGUAGES` yoki model yo'li sozlamalari bilan
  bu papkadan modelni topishi kerak.
- Agar foydalanuvchi boshqa modelni yuklab olgan bo'lsa, u quyidagi
  tartibda o'rnatilishi kerak:

  1. Arxivdan chiqargan modelni `models/` papkasiga joylang.
  2. Papka nomi `config.py` dagi model yo'liga mos kelishi kerak.
  3. Agar model nomi yoki yo'li o'zgargan bo'lsa, `config.py` ichidagi
     `vosk_model` qiymatini ham moslashtirish kerak.

## Modelni almashtirish uchun nima o'zgartirish kerak?

Agar foydalanuvchi boshqa modelni ishlatmoqchi bo'lsa, quyidagi joylarni tekshirish va
moslashtirish kerak:

- `config.py`
  - `LANGUAGES` lug'ati ichidagi `vosk_model` qiymati
  - model uchun mos til nomi va yo'li
- `main.py` yoki boshqa start punktlar (agar model yo'li hard-code bo'lsa)
- `ui/` ichidagi model tanlash logikasi (agar foydalanuvchi tanlovdan boshqa modelni tanlasa)

## Misol

```python
LANGUAGES = {
    "uzbek": {
        "vosk_model": "models/vosk-model-small-uz-0.22",
        # ...
    }
}
```

Yuqoridagi misoldagi yo'lga mos ravishda model fayllari `models/` papkasi ichida bo'lishi kerak.

## Eslatma

Agar modelni nomi yoki fayl tuzilmasi o'zgargan bo'lsa, dastur ishlashi uchun `config.py`
ichidagi yo'llarni moslashtirish zarur bo'ladi.
