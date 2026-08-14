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
API_TOKEN = '8928908790:AAFIKHuyDTqI2DRT9T7sLLhYyVeZwdKseBU'
ADMIN_ID = 8853790254  # Your Telegram User ID
bot = telebot.TeleBot(API_TOKEN)

# RESET TELEGRAM MENU TO ONLY ACTIVE COMMANDS
try:
    bot.delete_my_commands()
    bot.set_my_commands([
        types.BotCommand("start", "Start the bot"),
        types.BotCommand("menu", "Open main menu"),
        types.BotCommand("help", "Show help & info"),
        types.BotCommand("get", "Get Player Dossier & Outfit"),
        types.BotCommand("guild", "Get Full Guild Information"),
        types.BotCommand("like", "Send Free Fire Likes")
    ])
except Exception as e:
    print(f"Command update notice: {e}")

# APIs
BIO_API_URL = "https://star-bio-api.lovable.app/api/public/bio-upload"
LIKE_API_URL = "https://najmi-ob54-like.vercel.app/like"
UNSUB_OTP_URL = "https://sso-register-killersharmabot.vercel.app/send-email"
GUILD_API_URL = "https://star-guild-info.lovable.app/api/public/info"

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

def fetch_player_data_by_uid_or_name(search_parameter):
    if search_parameter.isdigit():
        url = f"https://info.strikerxyash.online/player-info?uid={search_parameter}"
    else:
        url = f"https://info.strikerxyash.online/player-info?name={search_parameter}"
    
    try:
        response = requests.get(url, timeout=10)
        if response.status_code != 200:
            return None
        data = response.json()
        basic_info = data.get("basicInfo", {})
        return (
            basic_info.get("accountId", "N/A"),
            basic_info.get("nickname", "N/A"),
            basic_info.get("region", "Not Chosen"),
            data
        )
    except Exception as e:
        print(f"Player Info Error: {e}")
        return None

def fetch_outfit_image(player_data):
    basic_information = player_data.get("basicInfo", {})
    profile_information = player_data.get("profileInfo", {})

    equipped_weapons = basic_information.get("weaponSkinShows", [])
    equipped_outfits = profile_information.get("clothes", [])
    character_id = profile_information.get("avatarId", "102000007")

    outfit_ids = ",".join(
        str(item) for item in (equipped_outfits + equipped_weapons)
    ) if (equipped_outfits or equipped_weapons) else ""

    url = f"https://image.strikerxyash.online/outfit-image?avatar_id={character_id}&clothes={outfit_ids}"
    return url

def fetch_guild_info(clan_id, region="BD"):
    url = f"{GUILD_API_URL}?clan_id={clan_id}&region={region}"
    try:
        res = requests.get(url, timeout=10)
        if res.status_code == 200:
            return res.json()
        return None
    except Exception as e:
        print(f"Guild API Error: {e}")
        return None

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
        types.KeyboardButton("Revoke Access Token")
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
# MAIN INTERCEPTOR & ROUTER
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

    # Slash Commands
    if text in ['/start', '/menu']:
        welcome_msg = get_welcome_text(user_name, user_id)
        bot.send_message(message.chat.id, welcome_msg, reply_markup=get_main_menu(), parse_mode='HTML', disable_web_page_preview=True)

    elif text == '/help':
        help_text = (
            "🛠️ <b>VOID BOT COMMAND CATALOG</b> 🛠️\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "📌 <b>General Commands:</b>\n"
            "├─ <code>/start</code>\n"
            "├─ <code>/menu</code>\n"
            "└─ <code>/help</code>\n\n"
            "🎮 <b>Free Fire Tools:</b>\n"
            "├─ <code>/get [UID or Name]</code>\n"
            "├─ <code>/guild [Guild ID] [Region]</code>\n"
            "└─ <code>/like [Region] [UID]</code>\n\n"
            "📱 <b>Support:</b> @voidffx1"
        )
        bot.reply_to(message, help_text, parse_mode='HTML', disable_web_page_preview=True)

    elif text.startswith('/guild'):
        args = text.split()
        if len(args) < 2:
            bot.reply_to(message, "❗ <b>Usage:</b> <code>/guild &lt;Guild_ID&gt; [Region]</code>", parse_mode='HTML')
            return
        clan_id = args[1]
        region = args[2].upper() if len(args) > 2 else "BD"
        
        sent_msg = bot.reply_to(message, "⏳ <i>Fetching Guild Information...</i>", parse_mode='HTML')
        guild_data = fetch_guild_info(clan_id, region)
        
        if not guild_data or guild_data.get("status") != "success":
            bot.edit_message_text("❌ Guild details not found or invalid Guild ID/Region.", chat_id=message.chat.id, message_id=sent_msg.message_id)
            return

        guild_template = (
            "🏰 <b>GUILD FULL DOSSIER</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━\n"
            f"🆔 <b>Guild ID:</b> <code>{escape_html(guild_data.get('guild_id', clan_id))}</code>\n"
            f"⭐ <b>Guild Level:</b> {escape_html(guild_data.get('guild_level', 'N/A'))}\n"
            f"🌐 <b>Region:</b> {escape_html(guild_data.get('region', region))}\n"
            f"👑 <b>Owner UID:</b> <code>{escape_html(guild_data.get('guild_owner_id', 'N/A'))}</code>\n"
            "━━━━━━━━━━━━━━━━━━━━━\n"
            f"👥 <b>Members:</b> {escape_html(guild_data.get('current_members', '0'))} / {escape_html(guild_data.get('total_members', '0'))}\n"
            f"🏆 <b>Glory Points:</b> {escape_html(guild_data.get('glory_points', '0'))}\n"
            f"💬 <b>Bio:</b> <i>{escape_html(guild_data.get('guild_bio', 'None'))}</i>\n"
            "━━━━━━━━━━━━━━━━━━━━━"
        )
        bot.edit_message_text(guild_template, chat_id=message.chat.id, message_id=sent_msg.message_id, parse_mode='HTML')

    elif text.startswith('/get'):
        args = text.split(maxsplit=1)
        if len(args) < 2:
            bot.reply_to(message, "❗ <b>Usage:</b> <code>/get &lt;UID or Name&gt;</code>", parse_mode='HTML')
            return
        
        search_query = args[1].strip()
        sent_msg = bot.reply_to(message, "⏳ <i>Fetching player info & outfit...</i>", parse_mode='HTML')

        player_data_tuple = fetch_player_data_by_uid_or_name(search_query)
        if not player_data_tuple:
            bot.edit_message_text("❌ Player not found.", chat_id=message.chat.id, message_id=sent_msg.message_id)
            return

        account_id, nickname, region, full_data = player_data_tuple
        basic_info = full_data.get("basicInfo", {})
        outfit_img_url = fetch_outfit_image(full_data)

        dossier = (
            "🎮 <b>PLAYER DOSSIER</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━\n"
            f"👑 <b>Nickname:</b> {escape_html(nickname)}\n"
            f"🕹️ <b>UID:</b> <code>{escape_html(account_id)}</code>\n"
            f"🌐 <b>Region:</b> {escape_html(region)}\n"
            f"⭐ <b>Level:</b> {escape_html(basic_info.get('level', 'N/A'))}\n"
            f"❤️ <b>Likes:</b> {escape_html(basic_info.get('liked', 'N/A'))}\n"
            "━━━━━━━━━━━━━━━━━━━━━"
        )

        bot.delete_message(chat_id=message.chat.id, message_id=sent_msg.message_id)
        try:
            bot.send_photo(message.chat.id, photo=outfit_img_url, caption=dossier, parse_mode='HTML')
        except Exception:
            bot.send_message(message.chat.id, dossier, parse_mode='HTML')

    elif text.startswith('/like'):
        args = text.split()
        if len(args) < 3:
            bot.reply_to(message, "❗ <b>Usage:</b> <code>/like &lt;Region&gt; &lt;UID&gt;</code>", parse_mode='HTML')
            return
        region, uid = args[1], args[2]
        sent_msg = bot.reply_to(message, "⏳ <i>Processing likes...</i>", parse_mode='HTML')
        try:
            res = requests.get(f"{LIKE_API_URL}?uid={uid}&server_name={region}&key=NJM", timeout=10)
            data = res.json()
            template = (
                "<b>🎉 LIKES DISPATCHED 👍</b>\n"
                "━━━━━━━━━━━━━━━━━━━━━\n"
                f"👑 <b>Name:</b> {escape_html(data.get('PlayerNickname', 'N/A'))}\n"
                f"🕹️ <b>UID:</b> <code>{uid}</code>\n"
                f"❤️ <b>Likes Before:</b> {escape_html(data.get('LikesbeforeCommand', '0'))}\n"
                f"💚 <b>Likes After:</b> {escape_html(data.get('LikesafterCommand', '0'))}"
            )
            bot.edit_message_text(template, chat_id=message.chat.id, message_id=sent_msg.message_id, parse_mode='HTML')
        except Exception as e:
            bot.edit_message_text(f"❌ Error: <code>{escape_html(str(e))}</code>", chat_id=message.chat.id, message_id=sent_msg.message_id, parse_mode='HTML')

    # Reply Keyboard Handlers
    elif text in ["Single Unsubscribe OTP", "Unbind Email"]:
        msg = bot.reply_to(message, "📩 <b>Send Target Email address to dispatch Unsubscribe OTP:</b>", parse_mode='HTML')
        bot.register_next_step_handler(msg, process_send_unsub_otp)

    elif text == "Check Recovery Email":
        msg = bot.reply_to(message, "🔑 <b>Send your Access Token:</b>", parse_mode='HTML')
        bot.register_next_step_handler(msg, process_check_email)

    elif text == "Add Recovery Email":
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
    bot.remove_webhook()
    bot.infinity_polling(skip_pending=True)
