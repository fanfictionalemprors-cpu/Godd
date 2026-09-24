import os
import telebot
import pymupdf as fitz
from deep_translator import GoogleTranslator

# Railway environment variable se token lega
BOT_TOKEN = os.environ.get("BOT_TOKEN", "YOUR_TELEGRAM_BOT_TOKEN_HERE")
bot = telebot.TeleBot(BOT_TOKEN)

# /start command
@bot.message_handler(commands=['start'])
def send_welcome(message):
    welcome_text = (
        "नमस्कार! 👋\n\n"
        "1. मुझे कोई भी **Text Message** भेजें - मैं उसका हिंदी अनुवाद कर दूंगा।\n"
        "2. मुझे कोई भी **EPUB (.epub)** फ़ाइल भेजें - मैं उसका हिंदी अनुवाद कर दूंगा।"
    )
    bot.reply_to(message, welcome_text, parse_mode="Markdown")

# Normal Text Translation
@bot.message_handler(content_types=['text'])
def translate_text(message):
    bot.send_chat_action(message.chat.id, 'typing')
    try:
        translated = GoogleTranslator(source='auto', target='hi').translate(message.text)
        bot.reply_to(message, f"**अनुवाद (Hindi):**\n\n{translated}", parse_mode="Markdown")
    except Exception as e:
        bot.reply_to(message, "माफ़ कीजिए, अनुवाद करने में समस्या आई।")

# EPUB File Translation
@bot.message_handler(content_types=['document'])
def handle_document(message):
    file_name = message.document.file_name

    if not file_name.lower().endswith('.epub'):
        bot.reply_to(message, "कृपया केवल `.epub` फ़ाइल ही भेजें।")
        return

    bot.reply_to(message, "EPUB फ़ाइल मिल गई है, प्रोसेसिंग चालू है...")
    bot.send_chat_action(message.chat.id, 'typing')

    file_info = bot.get_file(message.document.file_id)
    downloaded_file = bot.download_file(file_info.file_path)
    file_path = f"./{file_name}"

    with open(file_path, 'wb') as new_file:
        new_file.write(downloaded_file)

    try:
        doc = fitz.open(file_path)
        extracted_text = ""
        
        # Read initial pages
        for page_num in range(min(3, len(doc))):
            extracted_text += doc[page_num].get_text()

        doc.close()

        if os.path.exists(file_path):
            os.remove(file_path)

        if not extracted_text.strip():
            bot.reply_to(message, "इस फ़ाइल से टेक्स्ट नहीं निकाला जा सका।")
            return

        # Translate text
        short_text = extracted_text[:1500]
        translated = GoogleTranslator(source='auto', target='hi').translate(short_text)

        response = (
            f"📚 **EPUB से निकाला गया अनुवाद (शुरुआती भाग):**\n\n"
            f"{translated}"
        )
        bot.reply_to(message, response)

    except Exception as e:
        if os.path.exists(file_path):
            os.remove(file_path)
        bot.reply_to(message, f"प्रोसेसिंग में एरर आया: {str(e)}")

print("Bot is starting...")
bot.infinity_polling()
