from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes
import edge_tts
import asyncio

BOT_TOKEN = "ضع_التوكن_هنا"

# قائمة الأصوات
voices = {
    "Ahmad": "ar-AhmedNeural",
    "Hamad": "ar-HamadNeural",
    "Hanan": "ar-HananNeural",
    "Fatima": "ar-FatimaNeural",
    "Salma": "ar-SalmaNeural"
}

# رسالة البداية مع اختيار الصوت
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton(name, callback_data=voice)] for name, voice in voices.items()]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("اختر الصوت:", reply_markup=reply_markup)

# عند اختيار الصوت
async def voice_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data['voice'] = query.data
    await query.edit_message_text(text=f"تم اختيار الصوت: {query.data}\nأرسل لي النص لتحويله إلى كلام.")

# تحويل النص إلى صوت
async def text_to_speech(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    voice = context.user_data.get('voice', 'ar-AhmedNeural')  # صوت افتراضي
    communicate = edge_tts.Communicate(user_text, voice)
    file_path = "output.mp3"
    await communicate.save(file_path)
    await update.message.reply_audio(open(file_path, 'rb'))

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(voice_selection))
    app.add_handler(CommandHandler("say", text_to_speech))
    app.run_polling()

if __name__ == "__main__":
    main()
