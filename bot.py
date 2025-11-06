import os
import asyncio
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters
import edge_tts

BOT_TOKEN = os.environ.get("BOT_TOKEN")  # ضع التوكن في متغير البيئة على Railway

# قائمة أصوات عربية متاحة
ARABIC_VOICES = [
    "ar-SY-AhmedNeural",   # صوت رجل
    "ar-SY-HalaNeural"     # صوت امرأة
]

# ===== رسالة البدء =====
async def start(update: Update, context):
    await update.message.reply_text(
        "🔥 مرحباً بك في بوت تحويل النص إلى صوت 🔥\n\n"
        "أرسل لي أي نص بالعربية وسأقوم بتحويله إلى صوت واضح جدًا 🎙️"
    )

# ===== دالة تحويل النص إلى صوت =====
async def text_to_speech(text: str, voice: str, filename: str):
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(filename)

# ===== التعامل مع الرسائل =====
async def handle_message(update: Update, context):
    text = update.message.text.strip()
    if not text:
        await update.message.reply_text("⚠️ أرسل نصًا لتحويله إلى صوت.")
        return

    await update.message.reply_text("⏳ جاري تحويل النص إلى صوت...")

    # اختيار صوت عشوائي من الأصوات المتاحة
    voice = ARABIC_VOICES[0] if len(text) % 2 == 0 else ARABIC_VOICES[1]
    filename = "output.mp3"

    try:
        await text_to_speech(text, voice, filename)
        # إرسال الملف للمستخدم
        with open(filename, "rb") as audio_file:
            await update.message.reply_audio(audio_file, caption="✅ تم تحويل النص إلى صوت!")
        os.remove(filename)
    except Exception as e:
        await update.message.reply_text(f"❌ حدث خطأ أثناء تحويل النص: {e}")

# ===== التشغيل =====
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("🚀 البوت يعمل الآن...")
    app.run_polling()

if __name__ == "__main__":
    main()
