import telebot
import requests
import urllib.parse
import json
import base64
import os
import html
from threading import Thread
from flask import Flask
from telebot import types
from telebot.apihelper import ApiTelegramException

# ==========================================
# FLASK WEB SERVER (Render Keep-Alive)
# ==========================================
app = Flask('')

@app.route('/')
def home():
    return "Void Free Fire Bot is Online!"

def run():
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)

# ==========================================
# BOT CONFIGURATION & SETUP
# ==========================================
API_TOKEN = '8928908790:AAFM4aujRYoPs5yE7LkmTu_aJu6vYMS4LQI'
ADMIN_ID = 8853790254  # Your Telegram User ID
bot = telebot.TeleBot(API_TOKEN)

# APIs
BIO_API_URL = "https://star-bio-api.lovable.app/api/public/bio-upload"
UNSUB_OTP_URL = "https://sso-register-killersharmabot.vercel.app/send-email"

# Required Channels for Force Sub
CHANNELS = [
    {"name": "📢 Main Channel", "username": "@voidofficials_ff", "link": "https://t.me/voidofficials_ff"},
    {"name": "📢 Official News", "username": "@official_void_ff", "link": "https://t.me/official_void_ff"}
]

TOKEN_TUTORIAL_URL = "https://sub2unlock.io/K37BS"

# ==========================================
# HELPER FUNCTIONS
# ==========================================
def escape_html(text):
    return html.escape(str(text)) if text is not None else "N/A"

def check_user_joined_all(user_id):
    for ch in CHANNELS:
        try:
            member = bot.get_chat_member(ch["username"], user_id)
            if member.status not in ['member', 'administrator', 'creator']:
                return False
        except ApiTelegramException as e:
            print(f"Force Sub Error for {ch['username']}: {e}")
            return False
    return True

# ==========================================
# KEYBOARD MENUS
# ==========================================
def get_main_menu():
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    markup.add(
        types.KeyboardButton("Check Recovery Email"),
        types.KeyboardButton("Add Recovery Email"),
        types.KeyboardButton("Change Bind Email"),
        types.KeyboardButton("Unbind Email"),
        types.KeyboardButton("Cancel Recovery Email"),
        types.KeyboardButton("Single Unsubscribe OTP"),
        types.KeyboardButton("Get Token Details"),
        types.KeyboardButton("Update bio"),
        types.KeyboardButton("Revoke Access Token"),
        types.KeyboardButton("Get Security Code")
    )
    return markup

def get_join_keyboard():
    markup = types.InlineKeyboardMarkup(row_width=1)
    for ch in CHANNELS:
        markup.add(types.InlineKeyboardButton(ch["name"], url=ch["link"]))
    markup.add(types.InlineKeyboardButton("✅ VERIFY", callback_data="check_subscription"))
    return markup

def get_welcome_text(user_name, user_id):
    return (
        "✨ 🌟 <b>WELCOME TO THE OFFICIAL VOID API BOT</b>✨\n\n"
        f"😎 <b>User:</b> {user_name}\n"
        f"👑 <b>ID:</b> <code>{user_id}</code>\n\n"
        "🔹 🚀 <b>Features:</b>\n\n"
        "• 📊 Check Bind Information\n"
        "• 🔗 Bind Email to Account\n"
        "• 🔓 Unbind Email\n"
        "• 🔄 Change Bind Email\n"
        "• ⚠️ Cancel Bind Request\n"
        "• 📩 Single Unsubscribe OTP\n"
        "• 🔐 Get Security Code\n"
        "• 🚫 Revoke Token\n\n"
        "🔑 <b>Don't know how to get Access Token?</b>\n"
        f"👉 <a href='{TOKEN_TUTORIAL_URL}'>Click Here to Get Token</a>\n\n"
        "❤️ <b>Premium & Secure Tool</b>\n"
        "📱 <b>Support:</b> @voidffx1\n\n"
        "🔹 👇 <b>Select an option from the Keyboard below:</b>"
    )

# ==========================================
# VERIFICATION CALLBACK
# ==========================================
@bot.callback_query_handler(func=lambda call: call.data == "check_subscription")
def verify_callback(call):
    user_id = call.from_user.id
    if check_user_joined_all(user_id):
        bot.answer_callback_query(call.id, "✅ Verification Successful!", show_alert=True)
        bot.delete_message(call.message.chat.id, call.message.message_id)
        
        user_name = escape_html(call.from_user.first_name)
        welcome_msg = get_welcome_text(user_name, user_id)
        bot.send_message(call.message.chat.id, welcome_msg, reply_markup=get_main_menu(), parse_mode='HTML', disable_web_page_preview=True)
    else:
        bot.answer_callback_query(call.id, "❌ You haven't joined both channels yet! Please join and try again.", show_alert=True)

# ==========================================
# MAIN ROUTER & MESSAGE HANDLERS
# ==========================================
@bot.message_handler(func=lambda m: True)
def main_router(message):
    user_id = message.from_user.id
    user_name = escape_html(message.from_user.first_name)
    user_handle = f"@{message.from_user.username}" if message.from_user.username else "No Username"
    text = message.text

    print(f"📩 [{user_name} | {user_id}]: {text}")

    # Log to admin
    if user_id != ADMIN_ID:
        try:
            log_text = (
                "📩 <b>NEW USER MESSAGE LOG</b>\n"
                "━━━━━━━━━━━━━━━━━━━━━\n"
                f"👤 <b>User:</b> {user_name} ({user_handle})\n"
                f"🆔 <b>ID:</b> <code>{user_id}</code>\n"
                f"💬 <b>Message:</b> {escape_html(text)}\n"
                "━━━━━━━━━━━━━━━━━━━━━"
            )
            bot.send_message(ADMIN_ID, log_text, parse_mode='HTML')
        except Exception as e:
            print(f"Admin Log Forward Error: {e}")

    # Force Sub Check
    if not check_user_joined_all(user_id):
        msg_text = (
            "⚠️ <b>Verification Required!</b>\n\n"
            "To use this bot, you must join our official channels first:\n\n"
            "<i>Click the buttons below to join, then press VERIFY.</i>"
        )
        bot.send_message(message.chat.id, msg_text, reply_markup=get_join_keyboard(), parse_mode='HTML')
        return

    # Commands
    if text in ['/start', '/menu']:
        welcome_msg = get_welcome_text(user_name, user_id)
        bot.send_message(message.chat.id, welcome_msg, reply_markup=get_main_menu(), parse_mode='HTML', disable_web_page_preview=True)

    elif text == '/help':
        help_text = (
            "🛠️ <b>VOID BOT HELP</b> 🛠️\n"
            "━━━━━━━━━━━━━━━━━━━━━\n\n"
            "Use the custom menu buttons below to manage account binds, send OTPs, decode tokens, or update your bio.\n\n"
            "📱 <b>Support:</b> @voidffx1"
        )
        bot.reply_to(message, help_text, parse_mode='HTML', disable_web_page_preview=True)

    # Reply Keyboard Handlers
    elif text in ["Single Unsubscribe OTP", "Unbind Email"]:
        msg = bot.reply_to(message, "📩 <b>Send Target Email address to dispatch Unsubscribe OTP:</b>", parse_mode='HTML')
        bot.register_next_step_handler(msg, process_send_unsub_otp)

    elif text == "Check Recovery Email":
        msg = bot.reply_to(message, "🔑 <b>Send your Access Token:</b>", parse_mode='HTML')
        bot.register_next_step_handler(msg, process_check_email)

    elif text in ["Add Recovery Email", "Change Bind Email"]:
        msg = bot.reply_to(message, "🔑 <b>Step 1:</b> Send your Access Token:", parse_mode='HTML')
        bot.register_next_step_handler(msg, step_add_email_token)

    elif text == "Cancel Recovery Email":
        msg = bot.reply_to(message, "🔑 <b>Send your Access Token to cancel pending bind:</b>", parse_mode='HTML')
        bot.register_next_step_handler(msg, process_cancel_bind)

    elif text == "Revoke Access Token":
        msg = bot.reply_to(message, "🔑 <b>Send your Access Token to revoke:</b>", parse_mode='HTML')
        bot.register_next_step_handler(msg, process_revoke_token)

    elif text == "Get Token Details":
        msg = bot.reply_to(message, "🔍 <b>Send your Access Token / JWT to decode:</b>", parse_mode='HTML')
        bot.register_next_step_handler(msg, process_decode_token)

    elif text == "Get Security Code":
         msg = bot.reply_to(message, "🔐 <b>Send your Access Token:</b>", parse_mode='HTML')
         bot.register_next_step_handler(msg, process_get_security_code)

    elif text == "Update bio":
        msg = bot.reply_to(message, "📝 <b>Send Access Token and new bio text separated by space:</b>", parse_mode='HTML')
        bot.register_next_step_handler(msg, process_update_bio)

# ==========================================
# STEP HANDLERS
# ==========================================
def process_send_unsub_otp(message):
    email = message.text.strip()
    sent_msg = bot.reply_to(message, "⏳ <i>Sending Single Unsubscribe OTP...</i>", parse_mode='HTML')
    
    try:
        res = requests.get(f"{UNSUB_OTP_URL}?email={email}", timeout=10)
        if res.status_code == 200:
            data = res.json()
            result_code = data.get("response", {}).get("result", -1)
            if result_code == 0:
                resp_text = (
                    "📩 <b>UNSUBSCRIBE OTP SENT SUCCESSFULLY</b>\n"
                    "━━━━━━━━━━━━━━━━━━━━━\n"
                    f"📧 <b>Target Email:</b> <code>{escape_html(email)}</code>\n"
                    "✅ <b>Status:</b> Success (Result: 0)\n"
                    "━━━━━━━━━━━━━━━━━━━━━"
                )
                bot.edit_message_text(resp_text, chat_id=message.chat.id, message_id=sent_msg.message_id, parse_mode='HTML')
            else:
                bot.edit_message_text(f"❌ Failed to send OTP:\n<code>{html.escape(res.text)}</code>", chat_id=message.chat.id, message_id=sent_msg.message_id, parse_mode='HTML')
        else:
            bot.edit_message_text(f"❌ API Error {res.status_code}", chat_id=message.chat.id, message_id=sent_msg.message_id)
    except Exception as e:
        bot.edit_message_text(f"❌ Error: <code>{html.escape(str(e))}</code>", chat_id=message.chat.id, message_id=sent_msg.message_id, parse_mode='HTML')

def process_check_email(message):
    token = message.text.strip()
    url = "https://100067.connect.garena.com/game/account_security/bind:get_bind_info"
    params = {'app_id': "100067", 'access_token': token}
    headers = {'User-Agent': "GarenaMSDK/4.0.19P9(Redmi Note 5 ;Android 9;en;US;)"}
    try:
        res = requests.get(url, params=params, headers=headers, timeout=10)
        if res.status_code == 200:
            data = res.json()
            resp_text = (
                "📧 <b>BIND SECURITY INFO</b>\n"
                "━━━━━━━━━━━━━━━━━━━━━\n"
                f"● <b>Current Email:</b> <code>{data.get('email', 'None')}</code>\n"
                f"● <b>Pending Email:</b> <code>{data.get('email_to_be', 'None')}</code>\n"
                "━━━━━━━━━━━━━━━━━━━━━"
            )
            bot.reply_to(message, resp_text, parse_mode='HTML')
        else:
            bot.reply_to(message, f"❌ API Error {res.status_code}")
    except Exception as e:
        bot.reply_to(message, f"❌ Error: {str(e)}")

def step_add_email_token(message):
    token = message.text.strip()
    msg = bot.reply_to(message, "📧 <b>Step 2:</b> Enter target email to bind:", parse_mode='HTML')
    bot.register_next_step_handler(msg, step_add_email_send_otp, token)

def step_add_email_send_otp(message, token):
    email = message.text.strip()
    headers = {"User-Agent": "GarenaMSDK/4.0.30", "Content-Type": "application/x-www-form-urlencoded"}
    send_otp_url = "https://100067.connect.garena.com/game/account_security/bind:send_otp"
    data = {"email": email, "locale": "en_PK", "region": "PK", "app_id": "100067", "access_token": token}
    res = requests.post(send_otp_url, headers=headers, data=data)
    
    if '"result":0' in res.text.replace(" ", ""):
        msg = bot.reply_to(message, f"📩 OTP sent to <code>{email}</code>!\n\n<b>Enter OTP:</b>", parse_mode='HTML')
        bot.register_next_step_handler(msg, step_add_email_verify, token, email)
    else:
        bot.reply_to(message, f"❌ Failed to send OTP:\n<code>{html.escape(res.text)}</code>", parse_mode='HTML')

def step_add_email_verify(message, token, email):
    otp = message.text.strip()
    headers = {"User-Agent": "GarenaMSDK/4.0.30", "Content-Type": "application/x-www-form-urlencoded"}
    verify_url = "https://100067.connect.garena.com/game/account_security/bind:verify_otp"
    data = {"app_id": "100067", "access_token": token, "email": email, "code": otp, "otp": otp, "type": "1"}
    res = requests.post(verify_url, headers=headers, data=data)
    
    try:
        verifier_token = res.json().get("verifier_token")
        if verifier_token:
            msg = bot.reply_to(message, "🔐 <b>Set a 6-digit secondary password:</b>", parse_mode='HTML')
            bot.register_next_step_handler(msg, step_add_email_final, token, email, verifier_token)
        else:
            bot.reply_to(message, f"❌ Verification failed:\n<code>{html.escape(res.text)}</code>", parse_mode='HTML')
    except Exception as e:
        bot.reply_to(message, f"❌ Error: {e}")

def step_add_email_final(message, token, email, verifier_token):
    sec_code = message.text.strip()
    headers = {"User-Agent": "GarenaMSDK/4.0.30", "Content-Type": "application/x-www-form-urlencoded"}
    bind_url = "https://100067.connect.garena.com/game/account_security/bind:create_bind_request"
    data = {"email": email, "app_id": "100067", "access_token": token, "verifier_token": verifier_token, "secondary_password": sec_code}
    
    res = requests.post(bind_url, headers=headers, data=data)
    if '"result":0' in res.text.replace(" ", ""):
        bot.reply_to(message, f"✅ <b>Bind Request Created!</b> for <code>{email}</code>", parse_mode='HTML')
    else:
        bot.reply_to(message, f"❌ Bind Request Failed:\n<code>{html.escape(res.text)}</code>", parse_mode='HTML')

def process_get_security_code(message):
    token = message.text.strip()
    url = "https://100067.connect.garena.com/game/account_security/bind:get_bind_info"
    params = {'app_id': "100067", 'access_token': token}
    headers = {'User-Agent': "GarenaMSDK/4.0.19P9(Redmi Note 5 ;Android 9;en;US;)"}
    
    try:
        res = requests.get(url, params=params, headers=headers, timeout=10)
        if res.status_code == 200:
            data = res.json()
            security_code = data.get('security_code', 'Not available')
            
            resp_text = (
                "🔐 <b>SECURITY CODE INFO</b>\n"
                "━━━━━━━━━━━━━━━━━━━━━\n"
                f"● <b>Security Code:</b> <code>{security_code}</code>\n"
                f"● <b>Current Email:</b> <code>{data.get('email', 'None')}</code>\n"
                "━━━━━━━━━━━━━━━━━━━━━"
            )
            bot.reply_to(message, resp_text, parse_mode='HTML')
        else:
            bot.reply_to(message, f"❌ API Error {res.status_code}")
    except Exception as e:
        bot.reply_to(message, f"❌ Error: {str(e)}")

def process_cancel_bind(message):
    token = message.text.strip()
    url = "https://100067.connect.garena.com/game/account_security/bind:cancel_request"
    headers = {"User-Agent": "GarenaMSDK/4.0.30", "Content-Type": "application/x-www-form-urlencoded"}
    data = {"app_id": "100067", "access_token": token}
    res = requests.post(url, headers=headers, data=data)
    
    if '"result":0' in res.text.replace(" ", ""):
        bot.reply_to(message, "✅ <b>Pending bind request cancelled!</b>", parse_mode='HTML')
    else:
        bot.reply_to(message, f"❌ Failed to cancel:\n<code>{html.escape(res.text)}</code>", parse_mode='HTML')

def process_revoke_token(message):
    token = message.text.strip()
    headers = {"User-Agent": "Mozilla/5.0"}
    logout_url = f"https://100067.connect.garena.com/oauth/logout?access_token={token}"
    
    try:
        res = requests.get(logout_url, headers=headers, timeout=10)
        bot.reply_to(message, "✅ <b>Access token revoked/logged out!</b>", parse_mode='HTML')
    except Exception as e:
        bot.reply_to(message, f"❌ Error: {str(e)}")

def process_decode_token(message):
    token = message.text.strip()
    try:
        parts = token.split('.')
        if len(parts) >= 2:
            payload_b64 = parts[1] + '=' * (-len(parts[1]) % 4)
            decoded = json.loads(base64.b64decode(payload_b64))
            bot.reply_to(message, f"🔍 <b>Decoded Payload:</b>\n<code>{html.escape(json.dumps(decoded, indent=2))}</code>", parse_mode='HTML')
        else:
            bot.reply_to(message, "❌ Invalid JWT token format.")
    except Exception as e:
        bot.reply_to(message, f"❌ Decode Error: <code>{e}</code>", parse_mode='HTML')

def process_update_bio(message):
    try:
        parts = message.text.split(maxsplit=1)
        token, new_bio = parts[0], parts[1]
        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
        res = requests.post(BIO_API_URL, json={"bio": new_bio}, headers=headers, timeout=10)
        
        if res.status_code == 200:
            bot.reply_to(message, f"✅ <b>Bio updated to:</b>\n<i>{html.escape(new_bio)}</i>", parse_mode='HTML')
        else:
            bot.reply_to(message, f"❌ HTTP {res.status_code}")
    except Exception:
        bot.reply_to(message, "❗ Send token and new bio separated by space.", parse_mode='HTML')

# ==========================================
# START WEB SERVER & BOT
# ==========================================
if __name__ == "__main__":
    t = Thread(target=run)
    t.daemon = True
    t.start()
    
    print("🤖 Void Free Fire Bot is running...")
    
    # Safely clear old webhooks and start polling
    bot.delete_webhook(drop_pending_updates=True)
    bot.infinity_polling(skip_pending=True)