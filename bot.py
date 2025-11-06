import os
import asyncio
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
import edge_tts

# متغير البيئة لرمز البوت
BOT_TOKEN = os.environ.get("BOT_TOKEN")

# قائمة الأصوات العربية المتاحة
VOICES = {
    "female": "ar-SY-SalmaNeural",
    "male": "ar-SY-HamedNeural"
}

OUTPUT_FILE = "/app/output.mp3"  # مسار ثابت على Railway

# دالة التحويل للنطق
async def text_to_speech(text: str, voice_name: str):
    if not text.strip():
        raise ValueError("النص فارغ!")
    communicate = edge_tts.Communicate(text, VOICES.get(voice_name, VOICES["female"]))
    await communicate.save(OUTPUT_FILE)

# أوامر البوت
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "مرحبًا! أرسل لي أي نص وسأحوّله لصوت عربي.\n"
        "للاختيار بين صوت رجل أو امرأة، اكتب: /voice male أو /voice female"
    )

async def set_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.args and context.args[0].lower() in VOICES:
        context.user_data["voice"] = context.args[0].lower()
        await update.message.reply_text(f"تم تغيير الصوت إلى {context.args[0].lower()}")
    else:
        await update.message.reply_text("الرجاء اختيار صوت 'male' أو 'female'")

async def speak(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    voice = context.user_data.get("voice", "female")
    try:
        await text_to_speech(text, voice)
        await update.message.reply_audio(audio=open(OUTPUT_FILE, "rb"))
    except Exception as e:
        await update.message.reply_text(f"❌ حدث خطأ أثناء تحويل النص: {e}")

# تهيئة البوت
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("voice", set_voice))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, speak))
    app.run_polling()

if __name__ == "__main__":
    main()
