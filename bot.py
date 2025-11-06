import os
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters
import edge_tts

# ================= إعدادات البوت =================
BOT_TOKEN = os.getenv("BOT_TOKEN")  # ضع التوكن في متغيرات Railway

# أصوات عربية
VOICES = {
    "female": "ar-SY-SalmaNeural",
    "male": "ar-SY-HamedNeural"
}

VOICE_NAMES = {
    "female": "أنثى - SalmaNeural",
    "male": "ذكر - "
}

AUDIO_PATH = "voice.mp3"

# ================= دوال البوت =================

# بدء البوت
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "مرحبًا! 🌟\nأرسل لي أي نص بالعربية لأحوّله إلى صوت.\n"
        "يمكنك اختيار الصوت باستخدام /voice قبل الإرسال."
    )

# اختيار الصوت
async def voice_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("👩 أنثى", callback_data="female")],
        [InlineKeyboardButton("👨 ذكر", callback_data="male")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("اختر الصوت المطلوب:", reply_markup=reply_markup)

# حفظ اختيار الصوت
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    voice = query.data
    context.user_data['voice'] = voice
    await query.edit_message_text(f"✅ تم اختيار الصوت: {VOICE_NAMES[voice]}")

# تحويل النص إلى صوت
async def text_to_speech(text: str, voice: str):
    communicate = edge_tts.Communicate(text, VOICES[voice])
    await communicate.save(AUDIO_PATH)
    return AUDIO_PATH

# استقبال النصوص
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if not text:
        await update.message.reply_text("❌ النص فارغ! حاول مرة أخرى.")
        return

    voice = context.user_data.get("voice", "female")  # افتراضي أنثى

    msg = await update.message.reply_text("🔊 جاري تحويل النص إلى صوت...")
    try:
        audio_file = await text_to_speech(text, voice)
        with open(audio_file, "rb") as f:
            await update.message.reply_voice(voice=f)
        os.remove(audio_file)  # حذف الملف بعد الإرسال
        await msg.delete()
    except Exception as e:
        await msg.edit_text(f"❌ حدث خطأ أثناء التحويل:\n{e}")

# ================= تشغيل البوت =================
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("voice", voice_command))
    app.add_handler(CallbackQueryHandler(button))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    print("🤖 البوت يعمل...")
    app.run_polling()

if __name__ == "__main__":
    main()
