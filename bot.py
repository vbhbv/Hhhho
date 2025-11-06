import os
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
from gtts import gTTS

# استدعاء التوكن من متغير البيئة في Railway
BOT_TOKEN = os.getenv("BOT_TOKEN")

# دالة البدء
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 أهلاً بك!\nأرسل لي أي نص وسأحوله إلى صوت واضح باللغة العربية 🎙️"
    )

# دالة تحويل النص إلى صوت
async def tts_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()

    if not text:
        await update.message.reply_text("❗الرجاء إرسال نص لتحويله إلى صوت.")
        return

    try:
        # تحويل النص إلى صوت باستخدام gTTS
        tts = gTTS(text=text, lang='ar', slow=False)
        audio_path = "voice.mp3"
        tts.save(audio_path)

        # إرسال الملف الصوتي للمستخدم
        await update.message.reply_voice(voice=open(audio_path, "rb"))
        os.remove(audio_path)

    except Exception as e:
        await update.message.reply_text(f"⚠️ حدث خطأ أثناء التحويل: {e}")

# إعداد التطبيق
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, tts_handler))

    print("🤖 البوت يعمل الآن...")
    app.run_polling()

if __name__ == "__main__":
    main()
