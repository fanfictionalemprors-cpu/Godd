import os
import pymupdf as fitz
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters
from deep_translator import GoogleTranslator

# Logging Setup
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

BOT_TOKEN = os.environ.get("BOT_TOKEN", "YOUR_TELEGRAM_BOT_TOKEN_HERE")

# /start command handler
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_text = (
        "नमस्कार! 👋\n\n"
        "1. मुझे कोई भी **Text Message** भेजें - मैं उसका हिंदी अनुवाद कर दूंगा।\n"
        "2. मुझे कोई भी **EPUB (.epub)** फ़ाइल भेजें - मैं उसका हिंदी अनुवाद कर दूंगा।"
    )
    await update.message.reply_text(welcome_text)

# Normal Text Translator Handler
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    await update.message.reply_chat_action("typing")
    
    try:
        translated = GoogleTranslator(source='auto', target='hi').translate(user_text)
        await update.message.reply_text(f"**अनुवाद:**\n{translated}", parse_mode="Markdown")
    except Exception as e:
        await update.message.reply_text("अनुवाद करने में समस्या आई।")

# EPUB Document Handler
async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    document = update.message.document
    file_name = document.file_name

    if not file_name.lower().endswith('.epub'):
        await update.message.reply_text("कृपया केवल `.epub` फॉर्मेट की फ़ाइल ही भेजें।")
        return

    await update.message.reply_text("EPUB फ़ाइल मिल गई है, प्रोसेसिंग चालू है...")
    await update.message.reply_chat_action("typing")

    file_path = f"./{file_name}"

    try:
        file = await context.bot.get_file(document.file_id)
        await file.download_to_drive(file_path)

        doc = fitz.open(file_path)
        extracted_text = ""
        
        for page_num in range(min(3, len(doc))):
            extracted_text += doc[page_num].get_text()

        doc.close()
        if os.path.exists(file_path):
            os.remove(file_path)

        if not extracted_text.strip():
            await update.message.reply_text("इस EPUB फ़ाइल से कोई टेक्स्ट नहीं पढ़ा जा सका।")
            return

        short_text = extracted_text[:1500]
        translated = GoogleTranslator(source='auto', target='hi').translate(short_text)

        response = (
            f"📚 **EPUB से निकाला गया अनुवाद (शुरुआती भाग):**\n\n"
            f"{translated}"
        )
        await update.message.reply_text(response)

    except Exception as e:
        if os.path.exists(file_path):
            os.remove(file_path)
        await update.message.reply_text(f"EPUB प्रोसेस करने में एरर आया: {str(e)}")

if __name__ == '__main__':
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_document))

    print("Bot starting...")
    app.run_polling()
