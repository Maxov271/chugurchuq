# 📊 Hisobot Boshqaruv Telegram Boti

Python 3.13+, AsyncTeleBot, SQLite3 va APScheduler asosida qurilgan,
production muhitiga tayyor, Clean Architecture tamoyillariga asoslangan
kunlik/haftalik hisobot boshqaruv boti.

## 🚀 O'rnatish

```bash
# 1. Virtual environment yarating
python3.13 -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate

# 2. Kutubxonalarni o'rnating
pip install -r requirements.txt

# 3. .env faylini yarating
cp .env.example .env
# .env faylini ochib BOT_TOKEN va ADMIN_ID ni to'ldiring

# 4. Botni ishga tushiring
python main.py
```

## 📁 Loyiha tuzilishi

```
config/        — sozlamalar (.env orqali)
database/      — SQLite3 ulanish, sxema, repository qatlami
handlers/      — Telegram xabar/callback handlerlari (admin va user)
keyboards/     — Inline Keyboard generatorlari
scheduler/     — APScheduler vazifalari (eslatma, backup)
services/      — biznes-mantiq (user, report, reminder, statistics, export, backup)
middlewares/   — ruxsat tekshiruvi (admin_only, registered_user_only)
states/        — admin uchun ko'p bosqichli (FSM) holat boshqaruvchisi
media/         — foydalanuvchilardan kelgan media fayllar (agar lokal saqlansa)
logs/          — log fayllar (rotatsiya bilan)
exports/       — TXT/CSV/XLSX/PDF eksport fayllari
backups/       — avtomatik zaxira nusxalari
main.py        — kirish nuqtasi
```

## ✨ Asosiy imkoniyatlar

- **Ro'yxatga olingan foydalanuvchilar tizimi** — faqat admin qo'shgan foydalanuvchilar botdan foydalana oladi, har biriga ichki ID (CH-001, CH-002, ...) beriladi.
- **Individual eslatma jadvali** — har bir foydalanuvchi uchun hafta kuni + vaqt + matn alohida belgilanadi.
- **Barcha media turlari** — matn, rasm, video, audio, voice, hujjat, location, contact qabul qilinadi.
- **Avtomatik chat tozalash** — hisobot yuborilgach, eslatma/hisobot/tugmalar foydalanuvchi chatidan o'chiriladi (ma'lumot bazada saqlanib qoladi).
- **To'liq admin paneli** — 95% Inline Keyboard orqali: hisobotlar, statistikalar, foydalanuvchilar, eksport, backup, qidiruv.
- **Faollik tahlili** — 1/7/30/90/180 kunlik faolsizlik bo'limlari, TOP 10 faol/sust foydalanuvchilar.
- **E'tibor talab qiluvchi foydalanuvchilar** — ketma-ket 3 marta javobsiz qolganlar avtomatik aniqlanadi.
- **4 xil eksport formati** — TXT, CSV, XLSX (openpyxl), PDF (reportlab, professional jadval ko'rinishida).
- **Avtomatik kunlik backup** — database + media + logs, APScheduler orqali.
- **Production-ready** — logging, exception handling, type hints, WAL rejimidagi SQLite, .env orqali maxfiy ma'lumotlar.

## ⚠️ Muhim eslatmalar

- `BOT_TOKEN` va `ADMIN_ID` hech qachon kodga yozilmagan — faqat `.env` orqali olinadi.
- Bir nechta admin kerak bo'lsa `.env` da `ADMIN_IDS=111,222,333` shaklida kiriting.
- Telegram API xabarni faqat ma'lum vaqt oralig'ida o'chirishga ruxsat beradi; juda eski xabarlarni o'chirishga urinish jim (log darajasida) e'tiborsiz qoldiriladi.
- FSM holatlari hozircha xotirada (`states/admin_states.py`) saqlanadi; bot qayta ishga tushirilsa, davom etayotgan bosqichlar tozalanadi. Katta yukda ishlaydigan tizim uchun buni Redis-ga ko'chirish tavsiya etiladi.

## 🔧 Kengaytirish g'oyalari

- `services/` qatlamiga yangi biznes-mantiq qo'shish orqali funksional kengaytirish oson.
- Yangi jadval kerak bo'lsa `database/models.py` ga qo'shing, so'ng `database/queries.py` da repository yozing.
- Yangi admin bo'limi kerak bo'lsa `keyboards/admin_keyboards.py` da tugma, `handlers/admin_handlers.py` da callback qo'shing.
