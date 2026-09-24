import os
import time
import telebot
import pymupdf as fitz
from deep_translator import GoogleTranslator

# Railway/Environment variables se Telegram Token padhega
BOT_TOKEN = os.environ.get("BOT_TOKEN", "YOUR_TELEGRAM_BOT_TOKEN_HERE")
bot = telebot.TeleBot(BOT_TOKEN)

# Safe Translation helper (bina block hue translate karne ke liye)
def safe_translate_text(text_chunk, target_lang='hi'):
    try:
        return GoogleTranslator(source='auto', target=target_lang).translate(text_chunk)
    except Exception as e:
        time.sleep(1)
        return text_chunk

# /start command
@bot.message_handler(commands=['start'])
def send_welcome(message):
    welcome_text = (
        "नमस्कार! 👋\n\n"
        "मुझे कोई भी **Document (.epub, .pdf, .txt)** फ़ाइल भेजें (2-4 MB तक).\n"
        "मैं उसका हिंदी अनुवाद करके आपको दे दूंगा।"
    )
    bot.reply_to(message, welcome_text, parse_mode="Markdown")

# Document Handler (2-4 MB Document processing)
@bot.message_handler(content_types=['document'])
def handle_document(message):
    file_name = message.document.file_name.lower()
    
    # Check supported formats
    if not (file_name.endswith('.epub') or file_name.endswith('.pdf') or file_name.endswith('.txt')):
        bot.reply_to(message, "कृपया केवल `.epub`, `.pdf` या `.txt` फ़ाइल ही भेजें।")
        return

    bot.reply_to(message, "📄 फ़ाइल मिल गई है! प्रोसेसिंग चालू है...")
    bot.send_chat_action(message.chat.id, 'typing')

    # File Download
    file_info = bot.get_file(message.document.file_id)
    downloaded_file = bot.download_file(file_info.file_path)
    file_path = f"./{message.document.file_name}"

    with open(file_path, 'wb') as new_file:
        new_file.write(downloaded_file)

    try:
        extracted_text = ""

        # Processing PDF / EPUB files using PyMuPDF
        if file_name.endswith('.pdf') or file_name.endswith('.epub'):
            doc = fitz.open(file_path)
            for page in doc:
                extracted_text += page.get_text() + "\n"
            doc.close()
        
        # Processing TXT files
        elif file_name.endswith('.txt'):
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                extracted_text = f.read()

        if os.path.exists(file_path):
            os.remove(file_path)

        if not extracted_text.strip():
            bot.reply_to(message, "इस दस्तावेज़ से कोई टेक्स्ट नहीं पढ़ा जा सका।")
            return

        # Text chunking and translation (Max 1500 chars for quick response)
        text_to_translate = extracted_text[:2000]
        translated = safe_translate_text(text_to_translate, target_lang='hi')

        response = (
            f"📚 **दस्तावेज़ का अनुवाद (Hindi Translation):**\n\n"
            f"{translated}"
        )
        bot.reply_to(message, response)

    except Exception as e:
        if os.path.exists(file_path):
            os.remove(file_path)
        bot.reply_to(message, f"प्रोसेस करने में समस्या आई: {str(e)}")

print("Bot deployed and running...")
bot.infinity_polling()
