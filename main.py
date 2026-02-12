import telebot
import requests
import os
from flask import Flask
from threading import Thread
from urllib.parse import quote

# --- CONFIGURATION ---
API_TOKEN = '8572934178:AAF8WpWZA8nLw4bsgGR3eVP_nUbFX9iaz5M'
CHANNEL_ID = '@CatalystMystery'
CHANNEL_LINK = 'https://t.me/CatalystMystery'
PIKWY_TOKEN = '125'
PROXY_BASE_URL = "https://my-proxy-apii.vercel.app/api?url="
PORT = int(os.environ.get("PORT", 10000))

bot = telebot.TeleBot(API_TOKEN, parse_mode="MARKDOWN")
app = Flask('')

# --- WEB SERVER FOR RENDER ---
@app.route('/')
def home():
    return "Catalyst Mystery Bot is Live on Port 10000!"

def run_web_server():
    app.run(host='0.0.0.0', port=PORT)

# --- HELPER: FORCE JOIN CHECK ---
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
    markup.add(telebot.types.InlineKeyboardButton("✨ Join Catalyst Mystery", url=CHANNEL_LINK))
    markup.add(telebot.types.InlineKeyboardButton("🔄 Verify Subscription", callback_data="check_sub"))
    
    text = (f"🚀 *Welcome, {user_name}!*\n\n"
            "I am the **Ultimate Web Snapshot Bot**. Send me any URL, and I will capture it instantly.\n\n"
            "📢 *Note:* Membership of our official channel is required.")
    bot.reply_to(message, text, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "check_sub")
def verify_sub(call):
    if is_subscribed(call.from_user.id):
        bot.answer_callback_query(call.id, "✅ Access Granted!")
        bot.send_message(call.message.chat.id, "🔓 *Verified!* Now send me a website link.")
    else:
        bot.answer_callback_query(call.id, "⚠️ Please join the channel first!", show_alert=True)

@bot.message_handler(func=lambda message: True)
def handle_capture(message):
    if message.text.startswith('/'): return

    # Force Join Check
    if not is_subscribed(message.from_user.id):
        markup = telebot.types.InlineKeyboardMarkup()
        markup.add(telebot.types.InlineKeyboardButton("✨ Join Channel", url=CHANNEL_LINK))
        bot.reply_to(message, "🚫 *Access Denied!*\n\nYou must join @CatalystMystery to use this bot.", reply_markup=markup)
        return

    url = message.text
    if not url.startswith(("http://", "https://")):
        bot.reply_to(message, "❌ *Invalid Format!*\nURL must start with `http://` or `https://`.")
        return

    status_msg = bot.reply_to(message, "📡 *Routing through Proxy Engine...*")

    # 1. Construct Pikwy URL
    pikwy_url = (f"https://api.pikwy.com?tkn={PIKWY_TOKEN}&d=3000&u={url}"
                 f"&fs=0&w=1280&h=1200&s=100&z=100&f=jpg&rt=jweb")
    
    # 2. Encode for Proxy
    encoded_url = quote(pikwy_url, safe='')
    final_api_url = f"{PROXY_BASE_URL}{encoded_url}"

    try:
        # Extended timeout for Proxy + API processing
        response = requests.get(final_api_url, timeout=60)
        
        if response.status_code == 200:
            data = response.json()
            # Extracting from api_payload as per your successful test
            payload = data.get('api_payload', {})
            image_url = payload.get('iurl')
            
            if image_url:
                bot.edit_message_text("📸 *Capturing Snapshot...*", status_msg.chat.id, status_msg.message_id)
                bot.send_chat_action(message.chat.id, 'upload_photo')
                bot.send_photo(
                    message.chat.id, 
                    image_url, 
                    caption=f"✅ *Snapshot Completed*\n🌐 *Source:* {url}\n\n🔥 Powered by @CatalystMystery"
                )
                bot.delete_message(status_msg.chat.id, status_msg.message_id)
            else:
                bot.edit_message_text("⚠️ *API Error:* Could not retrieve image URL via Proxy.", status_msg.chat.id, status_msg.message_id)
        else:
            bot.edit_message_text(f"🚫 *Proxy Error:* Server returned status {response.status_code}", status_msg.chat.id, status_msg.message_id)
    except Exception as e:
        bot.edit_message_text("❌ *System Failure:* The request timed out or the URL is invalid.", status_msg.chat.id, status_msg.message_id)

# --- RUNNING ---
if __name__ == '__main__':
    # Start Keep-Alive Web Server
    Thread(target=run_web_server).start()
    print("Bot is starting with Proxy Integration...")
    bot.infinity_polling()
