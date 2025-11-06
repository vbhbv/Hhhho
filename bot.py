import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters, CallbackQueryHandler
import edge_tts
import os

# التوكن يجب وضعه في متغيرات البيئة Railway باسم BOT_TOKEN
BOT_TOKEN = os.environ.get("BOT_TOKEN")

# قائمة الأصوات العربية الحديثة
voices = {
    "Naama (female)": "ar-NaamaNeural",
    "Hamad (male)": "ar-HamadNeural"
}

# الدالة الرئيسية لتحويل النص إلى صوت
async def text_to_speech(text: str, voice_name: str, file_path: str):
    communicate = edge_tts.Communicate(text, voice=voice_name)
    await communicate.save(file_path)

# بدء البوت
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton(name, callback_data=name)] for name in voices.keys()]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("اختر صوتًا لتوليد الصوت من النص:", reply_markup=reply_markup)

# اختيار الصوت
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data['voice'] = voices[query.data]
    await query.edit_message_text(text=f"تم اختيار الصوت: {query.data}\nالآن أرسل النص لتحويله إلى صوت.")

# استقبال النص وتحويله
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    voice_name = context.user_data.get('voice', "ar-NaamaNeural")  # الصوت الافتراضي
    file_path = f"speech_{update.message.from_user.id}.mp3"
    
    try:
        await text_to_speech(text, voice_name, file_path)
        # إرسال الصوت للمستخدم
        with open(file_path, "rb") as audio_file:
            await update.message.reply_audio(audio_file)
        # حذف الملف بعد الإرسال لتجنب تراكم الملفات
        os.remove(file_path)
    except Exception as e:
        await update.message.reply_text(f"❌ حدث خطأ أثناء التحويل:\n{str(e)}")

# إعداد التطبيق
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    
    print("البوت يعمل الآن...")
    app.run_polling()

if __name__ == "__main__":
    main()
