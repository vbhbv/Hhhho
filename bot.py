import os
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from openai import OpenAI
import tempfile

# إعداد مفتاحي الـ Tokens
BOT_TOKEN = os.getenv("BOT_TOKEN")  # توكن البوت من متغيرات البيئة
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")  # مفتاح OpenAI من متغيرات البيئة

client = OpenAI(api_key=OPENAI_API_KEY)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🎙️ أرسل لي أي نص بالعربية وسأحوّله إلى صوت طبيعي فورًا 🔊")

async def text_to_speech(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    await update.message.reply_text("⏳ جارٍ توليد الصوت...")

    try:
        # توليد الصوت باستخدام gpt-4o-mini-tts
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp_file:
            response = client.audio.speech.create(
                model="gpt-4o-mini-tts",
                voice="alloy",  # يمكن لاحقاً استبداله بـ صوت آخر
                input=text
            )
            tmp_file.write(response.read())
            tmp_path = tmp_file.name

        await update.message.reply_audio(audio=open(tmp_path, "rb"), caption="✅ هذا هو صوت النص 🎧")

    except Exception as e:
        await update.message.reply_text(f"⚠️ حدث خطأ: {e}")

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_to_speech))

    print("🤖 Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
