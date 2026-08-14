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
# FLASK WEB SERVER (Render 24/7 Keep-Alive)
# ==========================================
app = Flask('')

@app.route('/')
def home():
    return "Void Free Fire Bot is Online!"

def run():
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)

# ==========================================
# BOT CONFIGURATION & ADMIN SETUP
# ==========================================
API_TOKEN = '8928908790:AAFRY0y4Q4JOxYhL__oB4Gznt6VxqlYlL7c'
ADMIN_ID = 8853790254  # Your Telegram User ID
bot = telebot.TeleBot(API_TOKEN)

# REGISTER BOT COMMAND MENU (AUTO-COMPLETE ON '/')
bot.set_my_commands([
    types.BotCommand("start", "Start the bot"),
    types.BotCommand("menu", "Open main menu"),
    types.BotCommand("help", "Show help & info"),
    types.BotCommand("get", "Get Player Dossier & Outfit"),
    types.BotCommand("guild", "Get Full Guild Information"),
    types.BotCommand("like", "Send Free Fire Likes"),
    types.BotCommand("ps", "Check Player Real Time Status"),
    types.BotCommand("bundle", "Bot will equip specific bundle"),
    types.BotCommand("emote", "Send any normal emote to squad"),
    types.BotCommand("lemote", "Send normal emote through loop"),
    types.BotCommand("evo_emote", "Send any evo emote to squad"),
    types.BotCommand("levo_emote", "Send all evo emote to squad"),
    types.BotCommand("5", "Create 5 player squad"),
    types.BotCommand("6", "Create 6 player squad")
])

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
# PLAYER & GUILD API HELPER FUNCTIONS
# ==========================================
def fetch_player_data_by_uid_or_name(search_parameter):
    """Fetches player info by UID or Name."""
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
    """Generates outfit avatar image URL based on character and clothes equipped."""
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
    """Fetches Guild full info from Star Guild Info API."""
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
    """Generates the main Reply Keyboard menu."""
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    markup.add(
        types.KeyboardButton("Check Recovery Email"),
        types.KeyboardButton("Add Recovery Email"),
        types.KeyboardButton("Change Bind Email"),
        types.KeyboardButton("Unbind Email"),
        types.KeyboardButton("Cancel Recovery Email"),
        types.KeyboardButton("Get Token Details"),
        types.KeyboardButton("Update bio"),
        types.KeyboardButton("Revoke Access Token")
    )
    return markup

def get_join_keyboard():
    """Generates the Inline Keyboard for channel subscription check."""
    markup = types.InlineKeyboardMarkup(row_width=1)
    for ch in CHANNELS:
        markup.add(types.InlineKeyboardButton(ch["name"], url=ch["link"]))
    markup.add(types.InlineKeyboardButton("✅ VERIFY", callback_data="check_subscription"))
    return markup

def get_welcome_text(user_name, user_id):
    """Generates the formatted welcome message with tutorial link."""
    return (
        "✨ 🌟 <b>WELCOME TO THE OFFICIAL VOID API BOT</b>✨\n\n"
        f"😎 <b>User:</b> {user_name}\n"
        f"👑 <b>ID:</b> <code>{user_id}</code>\n\n"
        "🔹 🚀 <b>Features:</b>\n\n"
        "• 📊 Check Bind Information\n"
        "• 🔗 Bind Email to Account\n"
        "• 🔓 Unbind Email & Send OTP\n"
        "• 🔄 Change Bind Email\n"
        "• 🏰 Guild Lookup\n"
        "• ⚠️ Cancel Bind Request\n"
        "• 🚫 Revoke Token\n\n"
        "🔑 <b>Don't know how to get Access Token?</b>\n"
        f"👉 <a href='{TOKEN_TUTORIAL_URL}'>Click Here to Get Token</a>\n\n"
        "❤️ <b>Premium & Secure Tool</b>\n"
        "📱 <b>Support:</b> @voidffx1\n\n"
        "🔹 👇 <b>Select an option from the Keyboard below:</b>"
    )

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

    # Print log to server console
    print(f"📩 [{user_name} | {user_id}]: {text}")

    # FORWARD USER MESSAGES TO ADMIN TELEGRAM ID
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

    # Slash Commands: /start & /menu
    if text in ['/start', '/menu']:
        welcome_msg = get_welcome_text(user_name, user_id)
        bot.send_message(message.chat.id, welcome_msg, reply_markup=get_main_menu(), parse_mode='HTML', disable_web_page_preview=True)

    # Slash Command: /help
    elif text == '/help':
        help_text = (
            "🛠️ <b>VOID BOT COMMAND CATALOG</b> 🛠️\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "📌 <b>General Commands:</b>\n"
            "├─ <code>/start</code>\n"
            "├─ <code>/menu</code>\n"
            "└─ <code>/help</code>\n\n"
            "🔑 <b>Token Tutorial:</b>\n"
            f"└─ <a href='{TOKEN_TUTORIAL_URL}'>How to Get Access Token</a>\n\n"
            "🎮 <b>Free Fire Player & Guild Lookup:</b>\n"
            "├─ <code>/get [UID or Name]</code>\n"
            "├─ <code>/guild [Guild ID] [Region]</code>\n"
            "└─ <code>/like [Region] [UID]</code>\n\n"
            "🤖 <b>Bot Actions:</b>\n"
            "├─ <code>/ps</code> - Check Player Real Time Status\n"
            "├─ <code>/bundle</code> - Equip specific bundle\n"
            "├─ <code>/emote</code> - Send emote to squad\n"
            "├─ <code>/lemote</code> - Send emote loop\n"
            "├─ <code>/evo_emote</code> - Send evo emote\n"
            "├─ <code>/levo_emote</code> - Send all evo emotes\n"
            "├─ <code>/5</code> - Create 5 player squad\n"
            "└─ <code>/6</code> - Create 6 player squad\n\n"
            "🔐 <b>Garena Account Security:</b>\n"
            "├─ Check Recovery Email\n"
            "├─ Add Recovery Email\n"
            "├─ Change Bind Email\n"
            "├─ Unbind Email\n"
            "├─ Cancel Recovery Email\n"
            "├─ Get Token Details\n"
            "└─ Revoke Access Token\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "📱 <b>Support & Inquiries:</b> @voidffx1"
        )
        bot.reply_to(message, help_text, parse_mode='HTML', disable_web_page_preview=True)

    # Custom Menu Commands Response
    elif text.startswith(('/ps', '/bundle', '/emote', '/lemote', '/evo_emote', '/levo_emote', '/5', '/6')):
        cmd = text.split()[0]
        bot.reply_to(message, f"⚙️ <b>Command <code>{cmd}</code> Received!</b>\n\n<i>This feature requires an active server session.</i>", parse_mode='HTML')

    # Slash Command: /guild <Guild ID> <Region>
    elif text.startswith('/guild'):
        args = text.split()
        if len(args) < 2:
            bot.reply_to(message, "❗ <b>Usage:</b> <code>/guild &lt;Guild_ID&gt; [Region]</code>\n<i>Example: /guild 3086500970 BD</i>", parse_mode='HTML')
            return
        
        clan_id = args[1]
        region = args[2].upper() if len(args) > 2 else "BD"
        
        sent_msg = bot.reply_to(message, "⏳ <i>Fetching Guild Information...</i>", parse_mode='HTML')
        guild_data = fetch_guild_info(clan_id, region)
        
        if not guild_data or guild_data.get("status") != "success":
            bot.edit_message_text("❌ Guild details not found or invalid Guild ID/Region.", chat_id=message.chat.id, message_id=sent_msg.message_id)
            return

        g_id = escape_html(guild_data.get("guild_id", clan_id))
        g_level = escape_html(guild_data.get("guild_level", "N/A"))
        g_region = escape_html(guild_data.get("region", region))
        g_owner = escape_html(guild_data.get("guild_owner_id", "N/A"))
        g_members = escape_html(guild_data.get("current_members", "0"))
        g_total = escape_html(guild_data.get("total_members", "0"))
        g_online = escape_html(guild_data.get("members_online", "0"))
        g_glory = escape_html(guild_data.get("glory_points", "0"))
        g_act = escape_html(guild_data.get("guild_activity_points", "0"))
        g_bio = escape_html(guild_data.get("guild_bio", "None"))
        g_rank = escape_html(guild_data.get("guild_position", "N/A"))
        created_at = escape_html(guild_data.get("created_at", "N/A"))

        guild_template = (
            "🏰 <b>GUILD FULL DOSSIER</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━\n"
            f"🆔 <b>Guild ID:</b> <code>{g_id}</code>\n"
            f"⭐ <b>Guild Level:</b> {g_level}\n"
            f"🌐 <b>Region:</b> {g_region}\n"
            f"👑 <b>Owner UID:</b> <code>{g_owner}</code>\n"
            "━━━━━━━━━━━━━━━━━━━━━\n"
            f"👥 <b>Members:</b> {g_members} / {g_total}\n"
            f"🟢 <b>Members Online:</b> {g_online}\n"
            f"🏆 <b>Glory Points:</b> {g_glory}\n"
            f"🔥 <b>Activity Points (XP):</b> {g_act}\n"
            f"📊 <b>Rank / Position:</b> #{g_rank}\n"
            f"📅 <b>Created At:</b> {created_at}\n"
            f"💬 <b>Guild Bio:</b> <i>{g_bio}</i>\n"
            "━━━━━━━━━━━━━━━━━━━━━"
        )
        bot.edit_message_text(guild_template, chat_id=message.chat.id, message_id=sent_msg.message_id, parse_mode='HTML')

    # Slash Command: /get <UID or Name>
    elif text.startswith('/get'):
        args = text.split(maxsplit=1)
        if len(args) < 2:
            bot.reply_to(message, "❗ <b>Usage:</b> <code>/get &lt;UID or Name&gt;</code>", parse_mode='HTML')
            return
        
        search_query = args[1].strip()
        sent_msg = bot.reply_to(message, "⏳ <i>Fetching player info & outfit...</i>", parse_mode='HTML')

        player_data_tuple = fetch_player_data_by_uid_or_name(search_query)
        if not player_data_tuple:
            bot.edit_message_text("❌ Player not found or API down.", chat_id=message.chat.id, message_id=sent_msg.message_id)
            return

        account_id, nickname, region, full_data = player_data_tuple
        basic_info = full_data.get("basicInfo", {})
        
        level = escape_html(basic_info.get("level", "N/A"))
        likes = escape_html(basic_info.get("liked", "N/A"))
        exp = escape_html(basic_info.get("exp", "N/A"))

        outfit_img_url = fetch_outfit_image(full_data)

        dossier = (
            "🎮 <b>PLAYER DOSSIER</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━\n"
            f"👑 <b>Nickname:</b> {escape_html(nickname)}\n"
            f"🕹️ <b>UID:</b> <code>{escape_html(account_id)}</code>\n"
            f"🌐 <b>Region:</b> {escape_html(region)}\n"
            f"⭐ <b>Level:</b> {level}\n"
            f"❤️ <b>Likes:</b> {likes}\n"
            f"📈 <b>EXP:</b> {exp}\n"
            "━━━━━━━━━━━━━━━━━━━━━"
        )

        bot.delete_message(chat_id=message.chat.id, message_id=sent_msg.message_id)
        try:
            bot.send_photo(message.chat.id, photo=outfit_img_url, caption=dossier, parse_mode='HTML')
        except Exception:
            bot.send_message(message.chat.id, dossier, parse_mode='HTML')

    # Slash Command: /like <Region> <UID>
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
            name = escape_html(data.get('PlayerNickname', 'N/A'))
            before = escape_html(data.get('LikesbeforeCommand', '0'))
            given = escape_html(data.get('LikesGivenByAPI', '0'))
            after = escape_html(data.get('LikesafterCommand', '0'))

            template = (
                "<b>🎉 LIKES DISPATCHED 👍</b>\n"
                "━━━━━━━━━━━━━━━━━━━━━\n"
                f"👑 <b>Name:</b> {name}\n"
                f"🕹️ <b>UID:</b> <code>{uid}</code>\n"
                f"🌐 <b>Region:</b> {region.upper()}\n"
                "━━━━━━━━━━━━━━━━━━━━━\n"
                f"❤️ <b>Likes Before:</b> {before}\n"
                f"🩵 <b>Likes Given:</b> {given}\n"
                f"💚 <b>Likes After:</b> {after}"
            )
            bot.edit_message_text(template, chat_id=message.chat.id, message_id=sent_msg.message_id, parse_mode='HTML')
        except Exception as e:
            bot.edit_message_text(f"❌ Error: <code>{escape_html(str(e))}</code>", chat_id=message.chat.id, message_id=sent_msg.message_id, parse_mode='HTML')

    # Reply Keyboard Options
    elif text == "Check Recovery Email":
        msg = bot.reply_to(message, f"🔑 <b>Send your Access Token:</b>\n\n<i>Don't have one? <a href='{TOKEN_TUTORIAL_URL}'>Click here</a></i>", parse_mode='HTML', disable_web_page_preview=True)
        bot.register_next_step_handler(msg, process_check_email)

    elif text == "Add Recovery Email":
        msg = bot.reply_to(message, f"🔑 <b>Step 1:</b> Send your Access Token:\n\n<i>Don't have one? <a href='{TOKEN_TUTORIAL_URL}'>Click here</a></i>", parse_mode='HTML', disable_web_page_preview=True)
        bot.register_next_step_handler(msg, step_add_email_token)

    elif text == "Unbind Email":
        msg = bot.reply_to(message, "📩 <b>Send the Target Email address to dispatch Unsubscribe OTP:</b>", parse_mode='HTML')
        bot.register_next_step_handler(msg, process_send_unsub_otp)

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
        msg = bot.reply_to(message, "📝 <b>Send Access Token and new bio text separated by space:</b>\n\n<i>Example: TOKEN My_New_Bio</i>", parse_mode='HTML')
        bot.register_next_step_handler(msg, process_update_bio)

    elif text in ["Change Bind Email"]:
        bot.reply_to(message, f"ℹ️ <b>{text}:</b> Send active token followed by your email/OTP to proceed.", parse_mode='HTML')

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
                bot.edit_message_text(f"❌ Failed to send OTP. Server Response:\n<code>{html.escape(res.text)}</code>", chat_id=message.chat.id, message_id=sent_msg.message_id, parse_mode='HTML')
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
            email = data.get("email", "None")
            email_to_be = data.get("email_to_be", "None")
            
            resp_text = (
                "📧 <b>BIND SECURITY INFO</b>\n"
                "━━━━━━━━━━━━━━━━━━━━━\n"
                f"● <b>Current Email:</b> <code>{email if email else 'None'}</code>\n"
                f"● <b>Pending Email:</b> <code>{email_to_be if email_to_be else 'None'}</code>\n"
                "━━━━━━━━━━━━━━━━━━━━━"
            )
            bot.reply_to(message, resp_text, parse_mode='HTML')
        else:
            bot.reply_to(message, f"❌ Failed to fetch info. API Error {res.status_code}")
    except Exception as e:
        bot.reply_to(message, f"❌ Error: {str(e)}")

def step_add_email_token(message):
    token = message.text.strip()
    msg = bot.reply_to(message, "📧 <b>Step 2:</b> Enter the target email to bind:", parse_mode='HTML')
    bot.register_next_step_handler(msg, step_add_email_send_otp, token)

def step_add_email_send_otp(message, token):
    email = message.text.strip()
    headers = {"User-Agent": "GarenaMSDK/4.0.30", "Content-Type": "application/x-www-form-urlencoded"}
    send_otp_url = "https://100067.connect.garena.com/game/account_security/bind:send_otp"
    data = {"email": email, "locale": "en_PK", "region": "PK", "app_id": "100067", "access_token": token}
    
    res = requests.post(send_otp_url, headers=headers, data=data)
    if '"result":0' in res.text.replace(" ", "") or '"result": 0' in res.text:
        msg = bot.reply_to(message, f"📩 OTP sent to <code>{email}</code>!\n\n<b>Enter the OTP received:</b>", parse_mode='HTML')
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
            msg = bot.reply_to(message, "🔐 <b>Set a 6-digit security code for this bind:</b>", parse_mode='HTML')
            bot.register_next_step_handler(msg, step_add_email_final, token, email, verifier_token)
        else:
            bot.reply_to(message, f"❌ OTP verification failed:\n<code>{html.escape(res.text)}</code>", parse_mode='HTML')
    except Exception as e:
        bot.reply_to(message, f"❌ Error parsing response: {e}")

def step_add_email_final(message, token, email, verifier_token):
    sec_code = message.text.strip()
    headers = {"User-Agent": "GarenaMSDK/4.0.30", "Content-Type": "application/x-www-form-urlencoded"}
    bind_url = "https://100067.connect.garena.com/game/account_security/bind:create_bind_request"
    data = {"email": email, "app_id": "100067", "access_token": token, "verifier_token": verifier_token, "secondary_password": sec_code}
    
    res = requests.post(bind_url, headers=headers, data=data)
    if '"result":0' in res.text.replace(" ", "") or '"result": 0' in res.text:
        bot.reply_to(message, f"✅ <b>Bind Request Created!</b>\nTarget Email: <code>{email}</code>", parse_mode='HTML')
    else:
        bot.reply_to(message, f"❌ Bind Request Failed:\n<code>{html.escape(res.text)}</code>", parse_mode='HTML')

def process_cancel_bind(message):
    token = message.text.strip()
    url = "https://100067.connect.garena.com/game/account_security/bind:cancel_request"
    headers = {"User-Agent": "GarenaMSDK/4.0.30", "Content-Type": "application/x-www-form-urlencoded"}
    data = {"app_id": "100067", "access_token": token}
    
    res = requests.post(url, headers=headers, data=data)
    if '"result":0' in res.text.replace(" ", "") or '"result": 0' in res.text:
        bot.reply_to(message, "✅ <b>Pending bind request successfully cancelled!</b>", parse_mode='HTML')
    else:
        bot.reply_to(message, f"❌ Failed to cancel bind:\n<code>{html.escape(res.text)}</code>", parse_mode='HTML')

def process_revoke_token(message):
    token = message.text.strip()
    headers = {"User-Agent": "Mozilla/5.0"}
    refresh_token = "1380dcb63ab3a077dc05bdf0b25ba4497c403a5b4eae96d7203010eafa6c83a8"
    logout_url = f"https://100067.connect.garena.com/oauth/logout?access_token={token}&refresh_token={refresh_token}"
    
    try:
        res = requests.get(logout_url, headers=headers, timeout=10)
        if res.status_code == 200 and "error" not in res.text:
            bot.reply_to(message, "✅ <b>Access token successfully revoked and logged out!</b>", parse_mode='HTML')
        else:
            bot.reply_to(message, f"❌ Revoke Failed: <code>{html.escape(res.text)}</code>", parse_mode='HTML')
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
        token = parts[0]
        new_bio = parts[1]
        
        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
        res = requests.post(BIO_API_URL, json={"bio": new_bio}, headers=headers, timeout=10)
        if res.status_code == 200:
            bot.reply_to(message, f"✅ <b>Bio updated to:</b>\n<i>{html.escape(new_bio)}</i>", parse_mode='HTML')
        else:
            bot.reply_to(message, f"❌ Failed to update bio. API HTTP {res.status_code}")
    except Exception:
        bot.reply_to(message, "❗ <b>Usage:</b> Send token and new bio text separated by space.", parse_mode='HTML')

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

```
