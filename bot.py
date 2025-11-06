import os
import asyncio
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, filters, ContextTypes
import edge_tts

# تحميل توكن البوت من متغير البيئة
BOT_TOKEN = os.getenv("BOT_TOKEN")

# أصوات عربية من Microsoft Edge-TTS
VOICES = {
    "رجل": "ar-YoussefNeural",
    "امرأة": "ar-SalmaNeural",
}

# الأمر /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "👋 أهلاً بك في بوت تحويل النص إلى صوت 🎙️\n\n"
        "أرسل أي نص بالعربية وسأنطقه لك بصوت طبيعي.\n\n"
        "🔈 يمكنك اختيار الصوت:\n"
        "• /voice رجل — صوت عربي رجولي\n"
        "• /voice امرأة — صوت أنثوي واضح\n\n"
        "الافتراضي: صوت رجل 👨"
    )
    await update.message.reply_text(text)

# تغيير الصوت
async def set_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("❗ استخدم الأمر هكذا:\n/voice رجل أو /voice امرأة")
        return

    choice = context.args[0]
    if choice not in VOICES:
        await update.message.reply_text("❌ الصوت غير متاح. اختر: رجل أو امرأة.")
        return

    context.user_data["voice"] = VOICES[choice]
    await update.message.reply_text(f"✅ تم اختيار صوت {choice} بنجاح!")

# تحويل النص إلى صوت
async def text_to_speech(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if not text:
        await update.message.reply_text("❗ أرسل نصًا لأقوم بتحويله إلى صوت.")
        return

    voice = context.user_data.get("voice", VOICES["رجل"])
    file_path = f"output_{update.effective_user.id}.mp3"

    try:
        communicate = edge_tts.Communicate(text, voice)
        await communicate.save(file_path)
        await update.message.reply_voice(voice=open(file_path, "rb"))
    except Exception as e:
        await update.message.reply_text(f"⚠️ حدث خطأ أثناء تحويل النص إلى صوت:\n{e}")
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)

# تشغيل البوت
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("voice", set_voice))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_to_speech))

    print("✅ البوت يعمل الآن...")
    app.run_polling()

if __name__ == "__main__":
    main()
