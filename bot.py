import os
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters
from edge_tts import Communicate, list_voices

# احصل على التوكن من متغيرات البيئة
BOT_TOKEN = os.getenv("BOT_TOKEN")

# قائمة الأصوات المتاحة (نماذج عربية حديثة)
VOICES = {
    "male": "ar-SamiNeural",
    "female": "ar-HalaNeural"
}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "مرحباً! أرسل لي نصاً وسأحولّه إلى صوت.\n"
        "لإختيار الصوت استخدم: /voice male أو /voice female\n"
        "افتراضي: female"
    )

# اختيار الصوت
async def set_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.args and context.args[0].lower() in VOICES:
        context.user_data["voice"] = context.args[0].lower()
        await update.message.reply_text(f"تم اختيار الصوت: {context.args[0].lower()}")
    else:
        await update.message.reply_text("الصوت غير موجود. الخيارات: male, female")

# تحويل النص إلى صوت
async def tts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    voice_choice = context.user_data.get("voice", "female")
    voice_name = VOICES[voice_choice]

    try:
        communicate = Communicate(text, voice_name)
        file_path = f"tts_{update.message.message_id}.mp3"
        await communicate.save(file_path)
        await update.message.reply_audio(audio=open(file_path, "rb"))
        os.remove(file_path)  # حذف الملف بعد الإرسال
    except Exception as e:
        await update.message.reply_text(f"❌ حدث خطأ أثناء التحويل:\n{str(e)}")

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("voice", set_voice))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, tts))

    print("البوت جاهز للعمل!")
    app.run_polling()

if __name__ == "__main__":
    main()
