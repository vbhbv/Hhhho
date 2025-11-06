import os
import telebot
from google import genai
from google.genai.errors import APIError
import atexit

# استيراد الوظائف الإدارية من الملف المنفصل
import admin 

# -------------------------------------------------------------
# 1. الإعدادات والثوابت والمفاتيح
# -------------------------------------------------------------

BOT_TOKEN = '6807502954:AAH5tOwXCjRXtF65wQFEDSkYeFBYIgUjblg' 
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

# مُعرفات المسؤول والقناة الإجبارية (قابلة للتغيير عبر متغيرات البيئة)
# يجب أن يكون البوت مشرفاً في القناة
FORCED_CHANNEL_ID = os.environ.get("FORCED_CHANNEL_ID", None) 
FORCED_CHANNEL_LINK = os.environ.get("FORCED_CHANNEL_LINK", "https://t.me/your_channel_link") 

# ملف تخزين مُعرفات المستخدمين
USER_DB_FILE = 'user_ids.txt'
user_ids = set() 

# -------------------------------------------------------------
# 2. تهيئة المكتبات والعملاء
# -------------------------------------------------------------

if not BOT_TOKEN:
    print("❌ خطأ فادح: توكن تيليجرام غير موجود.")
    exit(1)

bot = telebot.TeleBot(BOT_TOKEN)
client = None
if GEMINI_API_KEY:
    try:
        client = genai.Client(api_key=GEMINI_API_KEY)
        print("✅ تم تهيئة عميل Gemini API بنجاح.")
    except Exception as e:
        print(f"❌ فشل تهيئة عميل Gemini: {e}")
        client = None

SYSTEM_PROMPT = (
    "أنت مدقق لغوي ومعلم نحو عربي قدير ومتخصص في الإعراب..." # (بقية التعليمات كما هي)
)

# -------------------------------------------------------------
# 3. وظائف إدارة المستخدمين والاشتراك
# -------------------------------------------------------------

def load_users():
    """تحميل مُعرفات المستخدمين من الملف عند بدء التشغيل."""
    global user_ids
    if os.path.exists(USER_DB_FILE):
        with open(USER_DB_FILE, 'r') as f:
            user_ids = set(line.strip() for line in f)
    print(f"تم تحميل {len(user_ids)} مُعرف مستخدم.")
    # تحديث user_ids في ملف admin.py
    admin.user_ids = user_ids

def save_users():
    """حفظ مُعرفات المستخدمين في الملف عند إغلاق البوت."""
    with open(USER_DB_FILE, 'w') as f:
        for user_id in admin.user_ids:
            f.write(f"{user_id}\n")
    print(f"تم حفظ {len(admin.user_ids)} مُعرف مستخدم.")

def add_user(user_id):
    """إضافة مُعرف مستخدم جديد وحفظه."""
    str_id = str(user_id)
    if str_id not in admin.user_ids:
        admin.user_ids.add(str_id)
        save_users() 

def get_forced_subscription_markup():
    """إنشاء لوحة المفاتيح للاشتراك الإجباري."""
    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(telebot.types.InlineKeyboardButton(
        text="قناة الاشتراك الإجباري 📢",
        url=FORCED_CHANNEL_LINK
    ))
    markup.add(telebot.types.InlineKeyboardButton(
        text="✅ تحقق من الاشتراك",
        callback_data='check_sub'
    ))
    return markup

def is_subscribed(user_id):
    """التحقق من حالة اشتراك المستخدم في القناة الإجبارية."""
    if not FORCED_CHANNEL_ID:
        return True

    try:
        member = bot.get_chat_member(FORCED_CHANNEL_ID, user_id)
        return member.status in ['member', 'creator', 'administrator']
    except Exception:
        # السماح بالمرور في حالة الخطأ لضمان استمرار البوت
        return True 

# -------------------------------------------------------------
# 4. وظائف البوت الرئيسية (الإعراب)
# -------------------------------------------------------------

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    add_user(message.chat.id)
    
    if FORCED_CHANNEL_ID and not is_subscribed(message.chat.id):
        bot.reply_to(message, 
                     "⚠️ **يجب عليك الاشتراك في القناة أولاً لاستخدام البوت.**\n"
                     "يرجى الضغط على زر الاشتراك ثم زر التحقق.", 
                     parse_mode='Markdown',
                     reply_markup=get_forced_subscription_markup())
        return

    bot.reply_to(message, 
                 "👋 مرحباً بك في بوت الإعراب الذكي!\n"
                 "أرسل لي أي جملة عربية وسأقوم بإعرابها إعراباً تفصيلياً وشاملاً لك.")

@bot.message_handler(content_types=['text'])
def handle_grammar_request(message):
    add_user(message.chat.id)
    
    if FORCED_CHANNEL_ID and not is_subscribed(message.chat.id):
         # (رسالة الاشتراك الإجباري)
        return
        
    user_text = message.text
    
    if len(user_text) < 3 or len(user_text) > 500: 
        bot.reply_to(message, "⚠️ يرجى إرسال جملة عربية واضحة تتراوح بين 3 و 500 حرف.")
        return

    status_message = bot.reply_to(message, "⏳ جارٍ تحليل الجملة نحويًا...")

    try:
        if not client:
            analysis_result = "❌ عذراً، لم يتم إعداد مفتاح Gemini API بشكل صحيح على الخادم."
        else:
            # الحصول على الإعراب من Gemini
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=user_text,
                config={"system_instruction": SYSTEM_PROMPT}
            )
            analysis_result = response.text
        
        bot.edit_message_text(analysis_result, status_message.chat.id, status_message.message_id, parse_mode='Markdown')

    except APIError as e:
        bot.edit_message_text("❌ عذراً، واجهت خطأً في الاتصال بخدمة الذكاء الاصطناعي.", status_message.chat.id, status_message.message_id)
    except Exception as e:
        bot.edit_message_text("❌ حدث خطأ غير متوقع.", status_message.chat.id, status_message.message_id)

# -------------------------------------------------------------
# 5. التشغيل
# -------------------------------------------------------------

if __name__ == '__main__':
    # تهيئة المتغيرات المشتركة في ملف admin.py
    admin.init_admin(bot, FORCED_CHANNEL_ID, FORCED_CHANNEL_LINK, save_users)
    
    # تحميل المستخدمين وبدء التشغيل
    load_users()
    atexit.register(save_users)
    
    print("🚀 بدء تشغيل بوت الإعراب...")
    try:
        bot.infinity_polling()
    except Exception as e:
        print(f"❌ فشل تشغيل البوت: {e}")
