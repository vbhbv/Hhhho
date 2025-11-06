import os
import telebot
from google import genai
from google.genai.errors import APIError
import atexit
import json

# استيراد ملف الإدارة
import admin 

# -------------------------------------------------------------
# 1. الإعدادات والثوابت والمفاتيح
# -------------------------------------------------------------

BOT_TOKEN = '6807502954:AAH5tOwXCjRXtF65wQFEDSkYeFBYIgUjblg' 
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

# يتم استبدال هذه المتغيرات بقراءة ملف settings.json
# FORCED_CHANNEL_ID = os.environ.get("FORCED_CHANNEL_ID", None) 
# FORCED_CHANNEL_LINK = os.environ.get("FORCED_CHANNEL_LINK", "https://t.me/your_channel_link") 

USER_DB_FILE = 'user_ids.txt'
SETTINGS_FILE = 'settings.json' 
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
    "أنت مدقق لغوي ومعلم نحو عربي قدير ومتخصص في الإعراب. "
    "مهمتك هي إعراب الجملة التي يرسلها المستخدم إعراباً تفصيلياً وشاملاً. "
    "يجب أن يكون الإعراب منظماً في شكل قائمة نقطية واضحة, ويجب أن تستخدم المصطلحات النحوية الفصحى. "
    "لا تضف أي مقدمات أو خاتمات للرد، فقط ابدأ بالإعراب مباشرةً."
)

# -------------------------------------------------------------
# 3. وظائف إدارة المستخدمين والإعدادات والاشتراك
# -------------------------------------------------------------

def load_settings():
    """تحميل إعدادات الاشتراك الإجباري من settings.json."""
    try:
        with open(SETTINGS_FILE, "r") as f: 
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError): 
        # قيم افتراضية آمنة
        return {"force_subscribe": False, "channel_id": None, "channel_link": "https://t.me/"}

def load_users():
    """تحميل مُعرفات المستخدمين من الملف عند بدء التشغيل."""
    global user_ids
    if os.path.exists(USER_DB_FILE):
        with open(USER_DB_FILE, 'r') as f:
            user_ids = set(line.strip() for line in f)
    print(f"تم تحميل {len(user_ids)} مُعرف مستخدم.")

def save_users():
    """حفظ مُعرفات المستخدمين في الملف عند إغلاق البوت."""
    with open(USER_DB_FILE, 'w') as f:
        for user_id in user_ids:
            f.write(f"{user_id}\n")
    print(f"تم حفظ {len(user_ids)} مُعرف مستخدم.")

def add_user(user_id):
    """إضافة مُعرف مستخدم جديد وحفظه."""
    str_id = str(user_id)
    if str_id not in user_ids:
        user_ids.add(str_id)
        save_users() 

def get_forced_subscription_markup():
    """إنشاء لوحة المفاتيح للاشتراك الإجباري (يعتمد على load_settings)."""
    settings = load_settings()
    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(telebot.types.InlineKeyboardButton(
        text="قناة الاشتراك الإجباري 📢",
        url=settings.get("channel_link", "https://t.me/")
    ))
    markup.add(telebot.types.InlineKeyboardButton(
        text="✅ تحقق من الاشتراك",
        callback_data='check_sub'
    ))
    return markup

def is_subscribed(user_id, channel_id=None):
    """التحقق من حالة اشتراك المستخدم في القناة الإجبارية."""
    settings = load_settings()
    channel_id_to_check = settings.get("channel_id")
    
    if not settings.get("force_subscribe") or not channel_id_to_check: return True
    try:
        member = bot.get_chat_member(channel_id_to_check, user_id)
        return member.status in ['member', 'creator', 'administrator']
    except Exception: return True 


# -------------------------------------------------------------
# 4. وظائف البوت الرئيسية (الإعراب)
# -------------------------------------------------------------

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    add_user(message.chat.id)
    
    settings = load_settings() 
    
    # فحص الاشتراك الإجباري
    if settings.get("force_subscribe") and not is_subscribed(message.chat.id):
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
    
    settings = load_settings() 
    
    # فحص الاشتراك الإجباري
    if settings.get("force_subscribe") and not is_subscribed(message.chat.id):
        bot.reply_to(message, 
                     "⚠️ **يجب عليك الاشتراك في القناة أولاً لاستخدام البوت.**", 
                     parse_mode='Markdown', 
                     reply_markup=get_forced_subscription_markup())
        return
        
    user_text = message.text
    
    # تجنب إرسال أي نص قصير جداً أو طويل جداً
    if len(user_text) < 3 or len(user_text) > 500: 
        bot.reply_to(message, "⚠️ يرجى إرسال جملة عربية واضحة تتراوح بين 3 و 500 حرف.")
        return

    status_message = bot.reply_to(message, "⏳ جارٍ تحليل الجملة نحويًا...")

    try:
        if not client:
            analysis_result = "❌ عذراً، لم يتم إعداد مفتاح Gemini API بشكل صحيح على الخادم."
        else:
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=user_text,
                config={"system_instruction": SYSTEM_PROMPT}
            )
            analysis_result = response.text
        
        # حذف parse_mode لتجنب خطأ 400 (Parsing Error)
        bot.edit_message_text(analysis_result, status_message.chat.id, status_message.message_id) 

    except APIError as e:
        print(f"❌ خطأ في Gemini API: {e}")
        bot.edit_message_text("❌ عذراً، واجهت خطأً في الاتصال بخدمة الذكاء الاصطناعي. قد تكون الحصة المجانية قد استُنفدت.", status_message.chat.id, status_message.message_id)
    except Exception as e:
        print(f"❌ خطأ أثناء المعالجة: {e}")
        bot.edit_message_text("❌ حدث خطأ غير متوقع.", status_message.chat.id, status_message.message_id)


# -------------------------------------------------------------
# 5. التشغيل
# -------------------------------------------------------------

if __name__ == '__main__':
    # **التهيئة الحاسم:** تمرير الدوال الصحيحة لتسجيل لوحة التحكم
    admin.init_admin(
        bot, 
        is_subscribed,
        get_forced_subscription_markup,
        send_welcome
    )
    
    load_users()
    atexit.register(save_users)
    
    print("🚀 بدء تشغيل بوت الإعراب...")
    try:
        # هنا يتم تشغيل البوت والبدء في تلقي الأوامر، بما فيها /admin
        bot.infinity_polling()
    except Exception as e:
        print(f"❌ فشل تشغيل البوت: {e}")
