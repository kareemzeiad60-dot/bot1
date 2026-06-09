import os
import sys
import time
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton

# ==================== [ إعدادات البيانات ] ====================

API_ID = 25354792
         # ضع هنا الـ API ID الخاص بك (أرقام فقط بدون علامات تنصيص)
API_HASH = "90ca5d98ffc1730b7e291811bc525f75" # ضع هنا الـ API HASH الخاص بك بين علامات التنصيص
BOT_TOKEN = "8576552585:AAGtjbRTDkeO8KC7cEK3HdTDM0jHJ5X00S8" # ضع توكن البوت الخاص بك هنا

MY_TELEGRAM_ID =  5464602559 # ضع معرف حسابك الشخصي هنا (الذي ستتحكم منه)

# قائمة الرسائل المعالجة لمنع التكرار
processed_messages = set()

# وقت بدء البوت (لتجاهل الرسائل القديمة)
bot_start_time = time.time()

# ============================================================

DOWNLOAD_DIR = "./temp_media/"
if not os.path.exists(DOWNLOAD_DIR):
    os.makedirs(DOWNLOAD_DIR)

print("[1] جاري تهيئة الحساب والبوت...")

# إنشاء الجلسات وتحديد مسارها لضمان عدم حدوث تداخل
user_app = Client("user_session", api_id=API_ID, api_hash=API_HASH)
bot_app = Client("bot_session", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# ==================== [ جزء الحساب USERBOT ] ====================
# هذا الجزء يراقب الرسائل الواردة إلى حسابك في الخاص

@user_app.on_message(filters.private & (filters.photo | filters.video))
async def capture_media(client: Client, message: Message):
    # تجاهل الرسائل القديمة (قبل بدء البوت)
    if message.date.timestamp() < bot_start_time:
        return
    
    # منع معالجة نفس الرسالة مرتين
    if message.id in processed_messages:
        print(f"[⏭️ userbot] تم تجاهل رسالة مكررة (ID: {message.id})")
        return
    
    processed_messages.add(message.id)
    
    # طباعة فورا في الـ Terminal عند وصول أي ميديا
    sender_name = message.from_user.first_name if message.from_user else "مجهول"
    print(f"[💬 userbot] وصلت ميديا جديدة من: {sender_name} (ID: {message.from_user.id})")

    # حفظ جميع الصور والفيديوهات بدون شروط معقدة
    is_view_once = True
    
    if is_view_once:
        print("[🚨 userbot] تم اكتشاف وسائط! جاري التحميل فوراً...")
        try:
            # تجهيز مسار مخصص لكل ملف
            ext = "jpg" if message.photo else "mp4"
            file_name = f"{DOWNLOAD_DIR}media_{message.id}.{ext}"
            
            # تحميل الملف من سيرفرات تليجرام
            file_path = await message.download(file_name=file_name)
            
            if file_path and os.path.exists(file_path):
                print(f"[✅ userbot] تم تحميل الملف بنجاح محلياً: {file_path}")
                
                # صياغة الرسالة التي ستصلك في البوت الرسمي
                caption_text = (
                    f"🚨 **تم التقاط ميديا عرض لمرة واحدة!**\n\n"
                    f"👤 **المرسل:** {sender_name}\n"
                    f"🆔 **المعرف:** `{message.from_user.id}`\n"
                    f"نوع الملف: {'صورة 📸' if message.photo else 'فيديو 🎥'}"
                )
                
                # إرسال الملف إلى حسابك عبر البوت الرسمي
                if message.photo:
                    await bot_app.send_photo(chat_id=MY_TELEGRAM_ID, photo=file_path, caption=caption_text)
                elif message.video:
                    await bot_app.send_video(chat_id=MY_TELEGRAM_ID, video=file_path, caption=caption_text)
                
                print("[🚀 bot] تم إرسال الميديا إلى واجهة التحكم بنجاح.")
                
                # حذف الملف المؤقت للحفاظ على المساحة
                os.remove(file_path)
            else:
                print(f"[❌ userbot] فشل تحميل الملف (قد يكون تم فتحه بالفعل من الهاتف).")
        except Exception as e:
            print(f"[💥 userbot] حدث خطأ أثناء السحب أو الإرسال: {e}")


# ==================== [ جزء واجهة التحكم BOT ] ====================
# هذا الجزء يتفاعل معك أنت شخصياً داخل محادثة البوت الرسمي

@bot_app.on_message(filters.command("start") & filters.user(MY_TELEGRAM_ID))
async def bot_start(client: Client, message: Message):
    print(f"[🤖 bot] ضغطت على /start داخل البوت")
    await message.reply_text(
        "👋 **مرحباً بك في واجهة التحكم للبوت المزدوج!**\n\n"
        "النظام الآن مهيأ ومربوط بحسابك الشخصي لمراقبة وسحب وسائط (العرض لمرة واحدة) وتخزينها هنا.\n\n"
        "حالة النظام الحالية: 🟢 متصل ويعمل في الخلفية.",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("فحص حالة الاتصال ⚡", callback_data="check_status")]
        ])
    )

# الرد على الأزرار التفاعلية للتأكد من استجابة البوت
@bot_app.on_callback_query(filters.regex("check_status"))
async def inline_buttons(client: Client, query):
    print(f"[🤖 bot] تم الضغط على زر فحص الحالة")
    await query.answer("🟢 الاتصال مستقر وسريع!", show_alert=True)


# ==================== [ تشغيل النظام المزدوج ] ====================

if __name__ == "__main__":
    print("\n[+] جاري محاولة تشغيل النظام (الحساب + البوت)...")
    try:
        # بدء تشغيل العميلين
        user_app.start()
        print("[✅] تم تسجيل دخول الحساب (Userbot) بنجاح.")
        
        bot_app.start()
        print("[✅] تم تشغيل البوت الرسمي (Bot Token) بنجاح.")
        
        print("\n[🚀🚀🚀] النظام يعمل بكامل طاقته الآن!")
        print("-> اذهب الآن إلى البوت الخاص بك في التليجرام وأرسل أمر: /start")
        print("-> انتظر وصول أي صورة عرض لمرة واحدة على حسابك لمشاهدة السحب المباشر.\n")
        
        # إبقاء السكريبت يعمل مستمعاً للطلبات
        from pyrogram import idle
        idle()
        
    except Exception as start_error:
        print(f"\n[❌] فشل تشغيل النظام! خطأ في البيانات أو الاتصال: {start_error}")
    finally:
        # إغلاق آمن عند إيقاف السكريبت بـ Ctrl+C
        try:
            user_app.stop()
            bot_app.stop()
            print("[🏁] تم إغلاق النظام بأمان.")
        except:
            pass