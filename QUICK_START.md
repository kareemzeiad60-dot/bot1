# البدء السريع - البوت 🚀

## الخطوات الأساسية:

### 1️⃣ الحصول على المفاتيح

#### API ID و API Hash:
1. اذهب إلى: https://my.telegram.org
2. سجل الدخول برقم هاتفك
3. اضغط "API Development Tools"
4. انسخ API ID و API Hash

#### Bot Token:
1. افتح Telegram
2. ابحث عن: @BotFather
3. أرسل: `/newbot`
4. اتبع الخطوات
5. انسخ البوت توكن

#### Admin ID:
1. ابحث عن: @userinfobot
2. ابدأ المحادثة
3. انسخ رقم ID الخاص بك

---

### 2️⃣ تثبيت المتطلبات

```bash
pip install -r requirements.txt
```

---

### 3️⃣ تشغيل البوت

```bash
python bot.py
```

---

### 4️⃣ الإجابة على الأسئلة

البوت سيسأل عن:
- **ApiId** (الرقم من my.telegram.org)
- **ApiHash** (النص من my.telegram.org)
- **Bot Token** (من @BotFather)
- **Admin ID** (رقمك من @userinfobot)

---

### 5️⃣ استخدام البوت

في Telegram:

```
/start     → بدء البوت
/status    → حالة البوت
/settings  → عرض الإعدادات
/toggle    → تفعيل/تعطيل التحميل
/logs      → عرض السجلات
/help      → المزيد من الأوامر
/stop      → إيقاف البوت
```

---

## 🎯 ما الذي يفعله البوت؟

✅ يستقبل الصور والملفات المؤقتة (View-Once)  
✅ يحفظها قبل حذفها تلقائياً  
✅ يحفظها في Saved Messages  
✅ يُرسل لك إخطارات  
✅ يمكنك التحكم به من Telegram  

---

## ❓ مشاكل شائعة

### "cannot import name 'ChatBase'"
**الحل:** تم إصلاحها بالفعل في bot.py

### "Bot token is invalid"
**الحل:** تأكد من نسخ البوت توكن من @BotFather بشكل صحيح

### "Admin ID is invalid"
**الحل:** استخدم @userinfobot للحصول على معرفك الصحيح

### البوت لا يستقبل الرسائل
**الحل:** تأكد من:
1. API ID و API Hash صحيحة
2. البوت نشط في @BotFather

---

## 📚 المزيد من المعلومات

اقرأ `BOT_README.md` للتفاصيل الكاملة.
