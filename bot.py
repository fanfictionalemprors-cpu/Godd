import os
import telebot
import pymupdf as fitz
from deep_translator import GoogleTranslator

BOT_TOKEN = os.environ.get("BOT_TOKEN", "YOUR_TELEGRAM_BOT_TOKEN_HERE")
bot = telebot.TeleBot(BOT_TOKEN)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "नमस्कार! मुझे कोई भी टेक्स्ट या EPUB फ़ाइल भेजें, मैं उसका हिंदी में अनुवाद कर दूँगा।")

@bot.message_handler(content_types=['text'])
def translate_text(message):
    try:
        translated = GoogleTranslator(source='auto', target='hi').translate(message.text)
        bot.reply_to(message, f"**अनुवाद:**\n{translated}", parse_mode="Markdown")
    except Exception as e:
        bot.reply_to(message, "अनुवाद करने में समस्या आई।")

@bot.message_handler(content_types=['document'])
def handle_document(message):
    if not message.document.file_name.lower().endswith('.epub'):
        bot.reply_to(message, "कृपया केवल `.epub` फ़ाइल भेजें।")
        return

    bot.reply_to(message, "EPUB फ़ाइल प्रोसेस हो रही है...")
    
    file_info = bot.get_file(message.document.file_id)
    downloaded_file = bot.download_file(file_info.file_path)
    file_path = f"./{message.document.file_name}"

    with open(file_path, 'wb') as new_file:
        new_file.write(downloaded_file)

    try:
        doc = fitz.open(file_path)
        extracted_text = ""
        for page_num in range(min(3, len(doc))):
            extracted_text += doc[page_num].get_text()
        doc.close()

        if os.path.exists(file_path):
            os.remove(file_path)

        if not extracted_text.strip():
            bot.reply_to(message, "इस फ़ाइल से टेक्स्ट नहीं निकाला जा सका।")
            return

        translated = GoogleTranslator(source='auto', target='hi').translate(extracted_text[:1500])
        bot.reply_to(message, f"📚 **EPUB अनुवाद:**\n\n{translated}")

    except Exception as e:
        if os.path.exists(file_path):
            os.remove(file_path)
        bot.reply_to(message, f"एरर: {str(e)}")

print("Bot started...")
bot.infinity_polling()
