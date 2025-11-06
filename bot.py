import os
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, CallbackQueryHandler, filters
import edge_tts
from io import BytesIO

# التوكن من متغيرات البيئة
BOT_TOKEN = os.getenv("BOT_TOKEN")

# قائمة الأصوات العربية المتاحة
VOICES = {
    "female1": "ar-SY-SalmaNeural",
    "female2": "ar-SA-HindNeural",
    "male1": "ar-SY-HamedNeural",
    "male2": "ar-SA-FaisalNeural",
    "male3": "ar-EG-AhmedNeural"
}

# المستخدم يبدأ هنا
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("أنثى 1", callback_data="voice_female1"),
         InlineKeyboardButton("أنثى 2", callback_data="voice_female2")],
        [InlineKeyboardButton("ذكر 1", callback_data="voice_male1"),
         InlineKeyboardButton("ذكر 2", callback_data="voice_male2"),
         InlineKeyboardButton("ذكر 3", callback_data="voice_male3")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "مرحبًا! أرسل لي أي نص لتحويله إلى صوت.\nاختر صوتك أولاً:", reply_markup=reply_markup
    )

# اختيار الصوت
async def voice_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    voice_key = query.data.replace("voice_", "")
    context.user_data["voice"] = voice_key
    await query.edit_message_text(f"✅ تم اختيار الصوت: {voice_key}\nأرسل لي النص الآن.")

# تحويل النص إلى صوت
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if not text:
        await update.message.reply_text("❌ النص فارغ!")
        return

    voice_key = context.user_data.get("voice", "female1")
    msg = await update.message.reply_text("🔊 جاري تحويل النص...")

    try:
        communicate = edge_tts.Communicate(text, VOICES[voice_key])
        audio_stream = BytesIO()
        await communicate.save(audio_stream)
        audio_stream.seek(0)
        await update.message.reply_voice(voice=audio_stream)
        await msg.delete()
    except Exception as e:
        await msg.edit_text(f"❌ حدث خطأ أثناء التحويل:\n{e}")

# إعداد التطبيق
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(voice_selection, pattern="voice_"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.run_polling()

if __name__ == "__main__":
    main()
