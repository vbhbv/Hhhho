import telebot
import time
import threading
import json
import os

# ===== الثوابت والإعدادات (محلية) =====
ADMIN_ID = 6166700051  # مُعرف المسؤول الثابت
USERS_FILE = 'user_ids.txt'
SETTINGS_FILE = 'settings.json'

# ===== متغيرات مشتركة (يتم تهيئتها من الملف الرئيسي) =====
bot = None
is_subscribed_func = None 
get_forced_subscription_markup_func = None
send_welcome_func = None
user_ids = set() # يُستخدم لتخزين المُعرفات الحالية للإذاعة
broadcasting = False


def load_settings():
    """تحميل إعدادات الاشتراك الإجباري."""
    try:
        with open(SETTINGS_FILE, "r") as f: 
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError): 
        return {"force_subscribe": False, "channel_id": None, "channel_link": None}

def save_settings(settings):
    """حفظ إعدادات الاشتراك الإجباري."""
    with open(SETTINGS_FILE, "w") as f: 
        json.dump(settings, f)


def init_admin(main_bot, is_sub_f, get_markup_f, welcome_f):
    """تهيئة المتغيرات المشتركة من الملف الرئيسي."""
    global bot, is_subscribed_func, get_forced_subscription_markup_func, send_welcome_func
    
    bot = main_bot
    is_subscribed_func = is_sub_f
    get_forced_subscription_markup_func = get_markup_f
    send_welcome_func = welcome_f
    
    # التسجيل الحاسم لأمر /admin والـ Callbacks
    register_admin_handlers()

    
# -------------------------------------------------------------
# 1. لوحة التحكم والإحصائيات
# -------------------------------------------------------------

def get_admin_markup(settings):
    """إنشاء لوحة مفاتيح لوحة التحكم."""
    status = "✅ مفعل" if settings.get("force_subscribe") else "❌ معطل"
    markup = telebot.types.InlineKeyboardMarkup()
    markup.row(
        telebot.types.InlineKeyboardButton("📊 إحصائيات", callback_data='stats'),
        telebot.types.InlineKeyboardButton("📢 إرسال إذاعة", callback_data='broadcast_start')
    )
    markup.row(
        telebot.types.InlineKeyboardButton(f"⚡ الاشتراك الإجباري: {status}", callback_data='manage_subscription')
    )
    return markup

def admin_panel_start(message):
    """التعامل مع أمر /admin."""
    if message.chat.id != ADMIN_ID: return
    settings = load_settings()
    bot.reply_to(message, 
                 "🔧 لوحة التحكم:", 
                 reply_markup=get_admin_markup(settings))

# -------------------------------------------------------------
# 2. وظائف الإذاعة
# -------------------------------------------------------------

def start_broadcast_task(message):
    """وظيفة تُرسل الإذاعة إلى جميع المستخدمين في Thread منفصل."""
    global broadcasting
    bot.send_message(message.chat.id, "⏳ جاري إرسال الإذاعة إلى جميع المستخدمين...")
    
    success_count = 0
    failure_count = 0
    
    # نحتاج إلى إعادة تحميل user_ids هنا لضمان الحصول على أحدث قائمة
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'r') as f:
            current_user_ids = set(line.strip() for line in f)
    else:
        current_user_ids = set()

    
    list_users = list(current_user_ids)
    
    for user_id_str in list_users:
        if not broadcasting: break
        user_id = int(user_id_str)
        try:
            bot.copy_message(user_id, message.chat.id, message.message_id)
            success_count += 1
            time.sleep(0.05)
        except Exception:
            failure_count += 1
            # لا نحذف المستخدمين هنا، هذا مسؤولية الدالة save_users في bot.py

    broadcasting = False
    settings = load_settings()
    
    final_message = (
        f"✅ انتهت عملية الإذاعة!\n"
        f"تم الإرسال بنجاح إلى: {success_count} مستخدم.\n"
        f"فشل الإرسال (حظر/خطأ): {failure_count} مستخدم.\n"
        f"عدد المستخدمين الكلي: {len(current_user_ids)}"
    )
    bot.send_message(ADMIN_ID, final_message, reply_markup=get_admin_markup(settings))

# -------------------------------------------------------------
# 3. التعامل مع ردود الأفعال (Callbacks)
# -------------------------------------------------------------

def callback_admin_handler(call):
    chat_id = call.message.chat.id
    settings = load_settings()
    
    if chat_id != ADMIN_ID: 
        bot.answer_callback_query(call.id, "❌ ليس لديك صلاحية.")
        return

    data = call.data
    
    # 1. الإحصائيات
    if data == 'stats':
        
        if os.path.exists(USERS_FILE):
            with open(USERS_FILE, 'r') as f:
                current_user_ids = set(line.strip() for line in f)
        else:
            current_user_ids = set()
            
        stats_msg = f"📊 إحصائيات البوت:\n" \
                    f"عدد المستخدمين المسجلين: {len(current_user_ids)}\n" \
                    f"معرف القناة الإجبارية: {settings.get('channel_id') or 'غير مُحدد'}"
        bot.edit_message_text(stats_msg, chat_id, call.message.message_id, reply_markup=get_admin_markup(settings))
    
    # 2. بدء الإذاعة
    elif data == 'broadcast_start':
        global broadcasting
        if broadcasting:
            bot.answer_callback_query(call.id, "عملية الإذاعة قيد التنفيذ بالفعل.")
            return

        broadcasting = True
        sent = bot.edit_message_text(
            "📢 **ابدأ الإذاعة:**\n"
            "أرسل الرسالة التي تريد إذاعتها. ستبدأ الإذاعة تلقائياً بعد إرسال الرسالة.",
            chat_id, call.message.message_id, parse_mode='Markdown'
        )
        # تسجيل دالة الخطوة التالية للإذاعة
        bot.register_next_step_handler(sent, start_broadcast_task)

    # 3. إدارة الاشتراك الإجباري
    elif data == 'manage_subscription':
        
        # تبديل الحالة
        new_status = not settings.get("force_subscribe", False)
        settings["force_subscribe"] = new_status
        save_settings(settings)
        
        status = "✅ مفعل" if new_status else "❌ معطل"
        
        msg = f"⚡ الاشتراك الإجباري الآن: {status}\n"
        if new_status and not settings.get("channel_id"):
            msg += "📝 لم يتم تعيين قناة، يرجى إرسال مُعرِّف القناة (مثل: @channel_username) أو الـ ID السلبي الآن."
            # تفعيل حالة انتظار المدخل الإداري
            bot.register_next_step_handler(call.message, set_channel_id)
        
        bot.edit_message_text(msg, chat_id, call.message.message_id, reply_markup=get_admin_markup(settings))
        
    bot.answer_callback_query(call.id)
    
# -------------------------------------------------------------
# 4. معالج تعيين ID القناة
# -------------------------------------------------------------

def set_channel_id(message):
    if message.chat.id != ADMIN_ID: return
    
    channel_id = message.text.strip()
    settings = load_settings()
    
    # حفظ القناة (يمكن أن يكون ID أو Username)
    settings["channel_id"] = channel_id
    
    # محاولة إنشاء رابط تقريبي (باستخدام Username)
    if channel_id.startswith('@'):
        settings["channel_link"] = f"https://t.me/{channel_id.replace('@', '')}"
    else:
        # إذا كان ID رقمي، يجب على المسؤول أن يضع الرابط يدوياً
        settings["channel_link"] = "يرجى تعيين الرابط يدوياً"
        
    save_settings(settings)

    bot.reply_to(message, f"✅ تم تعيين القناة للاشتراك الإجباري:\n- ID/Username: `{channel_id}`\n- الرابط: {settings['channel_link']}", parse_mode='Markdown')
    admin_panel_start(message) # العودة للوحة التحكم

# -------------------------------------------------------------
# 5. تسجيل المعالجات
# -------------------------------------------------------------

def register_admin_handlers():
    """تسجيل جميع معالجات الأوامر الإدارية."""
    # أمر /admin
    bot.register_message_handler(admin_panel_start, commands=['admin'], func=lambda message: message.chat.id == ADMIN_ID)
    
    # معالجة ردود الأفعال (Callbacks)
    bot.register_callback_query_handler(callback_admin_handler, func=lambda call: call.data in ['stats', 'broadcast_start', 'manage_subscription'])
    
    # معالجة الـ callback الخاص بالتحقق من الاشتراك (يأتي من المستخدم العادي)
    bot.register_callback_query_handler(check_sub_callback, func=lambda call: call.data == 'check_sub')

def check_sub_callback(call):
    """معالج زر 'تحقق من الاشتراك' للمستخدم العادي."""
    chat_id = call.message.chat.id
    settings = load_settings()

    # التحقق من الاشتراك باستخدام الدالة الممررة من الملف الرئيسي
    if is_subscribed_func(chat_id, settings.get("channel_id")):
        bot.edit_message_text("✅ تم التحقق، يمكنك الآن استخدام البوت.", chat_id, call.message.message_id)
        # استدعاء دالة الترحيب لإعادة المستخدم إلى الحالة العادية
        if send_welcome_func:
             send_welcome_func(call.message) 
    else:
        bot.answer_callback_query(call.id, "❌ لم يتم تأكيد اشتراكك بعد. يرجى الاشتراك والضغط مرة أخرى.")
