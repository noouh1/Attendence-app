# 🎫 Attendance QR System — دليل الاستخدام

## المتطلبات
- Python 3.8+
- Excel file اسمه `people.xlsx` بعمودين على الأقل: `name` و `email`

---

## ⚡ التشغيل السريع

### الخطوة 0 — تثبيت المكتبات
```bash
pip install -r requirements.txt
```

---

### الخطوة 1 — توليد QR Codes
```bash
python 1_generate_qr.py
```
**الناتج:**
- فولدر `qr_codes/` فيه 450 صورة QR
- ملف `people_with_ids.xlsx` مُحدَّث بـ IDs وأعمدة الحضور

---

### الخطوة 2 — إرسال الإيميلات
افتح `2_send_emails.py` وعدّل:
```python
GMAIL_ADDRESS      = "your_email@gmail.com"
GMAIL_APP_PASSWORD = "xxxx xxxx xxxx xxxx"   # Gmail App Password
EVENT_NAME         = "اسم الفعالية"
```

ثم شغّل:
```bash
python 2_send_emails.py
```

> 📌 **Gmail App Password:**
> Google Account → Security → 2-Step Verification → App Passwords → Create

---

### الخطوة 3 — تطبيق المسح
```bash
python 3_attendance_app.py
```
افتح المتصفح على: **http://localhost:5000**

**للوصول من موبايل أو جهاز آخر على نفس الشبكة:**
```
http://YOUR_PC_IP:5000
```

**للوصول من الإنترنت (ngrok):**
```bash
pip install ngrok
ngrok http 5000
```

---

## 📁 هيكل الملفات
```
attendance_project/
├── people.xlsx                ← ملف الأشخاص (ضعه هنا)
├── people_with_ids.xlsx       ← ينتج بعد الخطوة 1
├── requirements.txt
├── 1_generate_qr.py
├── 2_send_emails.py
├── 3_attendance_app.py
├── templates/
│   └── scanner.html
└── qr_codes/                  ← ينتج بعد الخطوة 1
    ├── P0001.png
    ├── P0002.png
    └── ...
```

---

## 🔧 تخصيص الأعمدة
إذا أعمدة الـ Excel مختلفة، عدّل في الملفات:
```python
NAME_COLUMN  = "name"    # اسم عمود الأسماء
EMAIL_COLUMN = "email"   # اسم عمود الإيميلات
```

---

## ✅ مميزات التطبيق
- مسح QR تلقائي بالكاميرا
- إدخال يدوي للـ ID
- إشعار فوري باسم الشخص
- منع التسجيل المزدوج مع تحذير
- إحصائيات حية (حضروا / لم يحضروا / النسبة)
- تصدير Excel بضغطة زر

---

## ❓ أسئلة شائعة

**Q: الكاميرا لا تعمل؟**
A: تأكد من فتح الموقع بـ HTTPS أو localhost (الكاميرا تحتاج secure context)

**Q: إيميلات لم تُرسل؟**
A: تحقق من App Password وأن 2FA مفعّل على حسابك

**Q: أريد إعادة الإرسال لشخص واحد فقط؟**
A: عدّل `df.iterrows()` في `2_send_emails.py` لتصفية باسم أو ID معين
