import telebot
import time
import threading

# -------------------------------------------------------------
# 1. متغيرات مشتركة (يتم تهيئتها من ملف bot.py)
# -------------------------------------------------------------

bot = None
ADMIN_ID = 6166700051 # مُعرف المسؤول الثابت الذي طلبته
FORCED_CHANNEL_ID = None
FORCED_CHANNEL_LINK = None
user_ids = set()
save_users_func = None
send_welcome_func = None # دالة الترحيب من bot.py
broadcasting = False

def init_admin(main_bot, channel_id, channel_link, save_func, welcome_func):
    """تهيئة المتغيرات المشتركة من الملف الرئيسي (bot.py)."""
    global bot, FORCED_CHANNEL_ID, FORCED_CHANNEL_LINK, save_users_func, send_welcome_func
    bot = main_bot
    FORCED_CHANNEL_ID = channel_id
    FORCED_CHANNEL_LINK = channel_link
    save_users_func = save_func
    send_welcome_func = welcome_func
    
    # **التسجيل الحاسم:** تسجيل معالجات الأوامر بعد تهيئة البوت
    register_admin_handlers()

def is_subscribed_admin_check(user_id):
    """وظيفة مساعدة للتحقق من الاشتراك."""
    if not FORCED_CHANNEL_ID: return True
    try:
        member = bot.get_chat_member(FORCED_CHANNEL_ID, user_id)
        return member.status in ['member', 'creator', 'administrator']
    except Exception: return True


# -------------------------------------------------------------
# 2. لوحة التحكم والإحصائيات
# -------------------------------------------------------------

def get_admin_markup():
    """إنشاء لوحة مفاتيح لوحة التحكم."""
    markup = telebot.types.InlineKeyboardMarkup()
    markup.row(
        telebot.types.InlineKeyboardButton("📊 الإحصائيات", callback_data='stats'),
        telebot.types.InlineKeyboardButton("📢 إرسال إذاعة", callback_data='broadcast_start')
    )
    markup.row(
        telebot.types.InlineKeyboardButton("🔗 إعدادات الاشتراك الإجباري", callback_data='forced_sub_setup')
    )
    return markup

def admin_panel_start(message):
    """التعامل مع أمر /admin."""
    bot.reply_to(message, 
                 "لوحة تحكم المسؤول ⚙️:\n"
                 "اختر الإجراء المطلوب:", 
                 reply_markup=get_admin_markup())

# -------------------------------------------------------------
# 3. وظائف الإذاعة
# -------------------------------------------------------------

def start_broadcast_task(message):
    """وظيفة تُرسل الإذاعة إلى جميع المستخدمين في Thread منفصل."""
    global broadcasting
    bot.send_message(message.chat.id, "⏳ جاري إرسال الإذاعة إلى جميع المستخدمين...")
    
    success_count = 0
    failure_count = 0
    list_users = list(user_ids)
    
    for user_id_str in list_users:
        if not broadcasting:
            break
        user_id = int(user_id_str)
        try:
            # استخدام copy_message لإرسال الرسالة كما هي
            bot.copy_message(user_id, message.chat.id, message.message_id)
            success_count += 1
            time.sleep(0.05)
        except Exception as e:
            if 'bot was blocked by the user' in str(e):
                user_ids.discard(user_id_str)
            failure_count += 1
    
    broadcasting = False
    save_users_func()
    
    final_message = (
        f"✅ انتهت عملية الإذاعة!\n"
        f"تم الإرسال بنجاح إلى: {success_count} مستخدم.\n"
        f"فشل الإرسال (حظر/خطأ): {failure_count} مستخدم.\n"
        f"عدد المستخدمين الإجمالي المتبقي: {len(user_ids)}"
    )
    bot.send_message(ADMIN_ID, final_message, reply_markup=get_admin_markup())


# -------------------------------------------------------------
# 4. التعامل مع ردود الأفعال (Callbacks)
# -------------------------------------------------------------

def callback_admin_handler(call):
    chat_id = call.message.chat.id
    
    if call.data == 'stats':
        stats_msg = f"📊 إحصائيات البوت:\n" \
                    f"عدد المستخدمين النشطين: {len(user_ids)}\n" \
                    f"معرف المسؤول: {ADMIN_ID}\n" \
                    f"معرف القناة الإجبارية: {FORCED_CHANNEL_ID or 'غير مُحدد'}"
        bot.edit_message_text(stats_msg, chat_id, call.message.message_id, reply_markup=get_admin_markup())
    
    elif call.data == 'broadcast_start':
        global broadcasting
        if broadcasting:
            bot.answer_callback_query(call.id, "عملية الإذاعة قيد التنفيذ بالفعل.")
            return

        broadcasting = True
        sent = bot.edit_message_text(
            "📢 **ابدأ الإذاعة:**\n"
            "الآن، أرسل الرسالة (نص، صورة، فيديو، إلخ.) التي تريد إذاعتها. ستبدأ الإذاعة تلقائياً بعد إرسال الرسالة.",
            chat_id, call.message.message_id, parse_mode='Markdown'
        )
        
        bot.register_next_step_handler(sent, start_broadcast_task)

    elif call.data == 'forced_sub_setup':
        sub_status = "مُفعل" if FORCED_CHANNEL_ID else "غير مُفعل"
        setup_msg = (
            f"🔗 إعدادات الاشتراك الإجباري:\n"
            f"الحالة الحالية: **{sub_status}**\n"
            f"معرف القناة: `{FORCED_CHANNEL_ID or 'لا يوجد'}`\n"
            f"رابط القناة: {FORCED_CHANNEL_LINK}"
        )
        bot.edit_message_text(setup_msg, chat_id, call.message.message_id, parse_mode='Markdown', reply_markup=get_admin_markup())
    
    elif call.data == 'check_sub':
        if is_subscribed_admin_check(chat_id):
            bot.edit_message_text("✅ تم التحقق، يمكنك الآن استخدام البوت.", chat_id, call.message.message_id)
            # استدعاء دالة الترحيب من bot.py لتمكين المستخدم من الاستخدام
            if send_welcome_func:
                 send_welcome_func(call.message) 
        else:
            bot.answer_callback_query(call.id, "❌ لم يتم تأكيد اشتراكك بعد. يرجى الاشتراك والضغط مرة أخرى.")
    
    bot.answer_callback_query(call.id)

# -------------------------------------------------------------
# 5. تسجيل المعالجات
# -------------------------------------------------------------

def register_admin_handlers():
    """تسجيل جميع معالجات الأوامر الإدارية."""
    # أمر /admin
    bot.register_message_handler(admin_panel_start, commands=['admin'], func=lambda message: message.chat.id == ADMIN_ID)
    
    # معالجة ردود الأفعال (Callbacks)
    bot.register_callback_query_handler(callback_admin_handler, func=lambda call: call.data in ['stats', 'broadcast_start', 'forced_sub_setup', 'check_sub'])

