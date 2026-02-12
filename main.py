import telebot
import requests
import os
import random
from flask import Flask
from threading import Thread
from urllib.parse import quote

# --- CONFIGURATION ---
API_TOKEN = '8572934178:AAF8WpWZA8nLw4bsgGR3eVP_nUbFX9iaz5M'
CHANNEL_ID = '@CatalystMystery'
CHANNEL_LINK = 'https://t.me/CatalystMystery'
PIKWY_TOKEN = '125'
PORT = int(os.environ.get("PORT", 10000))

bot = telebot.TeleBot(API_TOKEN, parse_mode="MARKDOWN")
app = Flask('')

# --- PROFESSIONAL ASSETS (Background Only) ---
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
]

def get_secure_headers():
    """Generates professional request headers for stability."""
    random_ip = f"{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}"
    return {
        "User-Agent": random.choice(USER_AGENTS),
        "X-Forwarded-For": random_ip,
        "Referer": "https://www.google.com/",
        "Accept": "application/json"
    }

# --- WEB SERVER FOR RENDER ---
@app.route('/')
def home():
    return "Catalyst Mystery Professional Service is Active."

def run_web_server():
    app.run(host='0.0.0.0', port=PORT)

# --- HELPER: MEMBERSHIP CHECK ---
def is_subscribed(user_id):
    try:
        status = bot.get_chat_member(CHANNEL_ID, user_id).status
        return status in ['member', 'administrator', 'creator']
    except Exception:
        return False

# --- COMMANDS ---
@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_name = message.from_user.first_name
    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(telebot.types.InlineKeyboardButton("✨ Join Official Channel", url=CHANNEL_LINK))
    markup.add(telebot.types.InlineKeyboardButton("🔄 Verify Membership", callback_data="check_sub"))
    
    text = (f"👋 *Welcome, {user_name}!*\n\n"
            "I am your **Professional Web Snapshot Assistant**. Provide any website URL, and I will generate a high-quality capture for you.\n\n"
            "📢 *Requirement:* Please ensure you are a member of our official community to access this service.")
    bot.reply_to(message, text, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "check_sub")
def verify_sub(call):
    if is_subscribed(call.from_user.id):
        bot.answer_callback_query(call.id, "✅ Access Authorized")
        bot.send_message(call.message.chat.id, "🔓 *Service Activated!* Please send the website link you wish to capture.")
    else:
        bot.answer_callback_query(call.id, "⚠️ Membership Required", show_alert=True)

@bot.message_handler(func=lambda message: True)
def handle_capture(message):
    if message.text.startswith('/'): return

    if not is_subscribed(message.from_user.id):
        markup = telebot.types.InlineKeyboardMarkup()
        markup.add(telebot.types.InlineKeyboardButton("✨ Join Channel", url=CHANNEL_LINK))
        bot.reply_to(message, "🚫 *Access Restricted*\n\nPlease join @CatalystMystery to use this tool.", reply_markup=markup)
        return

    url = message.text
    if not url.startswith(("http://", "https://")):
        bot.reply_to(message, "❌ *Invalid Input*\nPlease provide a valid URL starting with `http` or `https`.")
        return

    status_msg = bot.reply_to(message, "🔄 *Establishing connection to the secure server...*")

    # API Configuration
    api_url = "https://api.pikwy.com"
    params = {
        "tkn": PIKWY_TOKEN, "d": "3000", "u": url,
        "fs": "0", "w": "1280", "h": "1200",
        "s": "100", "z": "100", "f": "jpg", "rt": "jweb"
    }

    try:
        # Secure background processing
        headers = get_secure_headers()
        bot.edit_message_text("⏳ *Processing high-resolution snapshot...*", status_msg.chat.id, status_msg.message_id)
        
        response = requests.get(api_url, params=params, headers=headers, timeout=50)
        
        if response.status_code == 200:
            data = response.json()
            image_url = data.get('iurl')
            
            if image_url:
                bot.send_chat_action(message.chat.id, 'upload_photo')
                bot.send_photo(
                    message.chat.id, 
                    image_url, 
                    caption=f"✅ *Snapshot Successfully Generated*\n🌐 *Domain:* {url}\n\n✨ Powered by @CatalystMystery"
                )
                bot.delete_message(status_msg.chat.id, status_msg.message_id)
            else:
                bot.edit_message_text("⚠️ *Service Notice:* Unable to render the requested page. Please check the URL.", status_msg.chat.id, status_msg.message_id)
        else:
            bot.edit_message_text("🚫 *Server Error:* The request could not be completed at this time.", status_msg.chat.id, status_msg.message_id)
    except Exception:
        bot.edit_message_text("❌ *System Timeout:* The connection was interrupted. Please try again.", status_msg.chat.id, status_msg.message_id)

# --- EXECUTION ---
if __name__ == '__main__':
    Thread(target=run_web_server).start()
    print("Professional Bot is Online...")
    bot.infinity_polling()
