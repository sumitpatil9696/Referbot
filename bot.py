import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import json
import os

TOKEN = "8785029829:AAG_fMM9KUx53QQlghr2klE6v9AbhiAQFuA"

# ---------- ADMINS ----------
ADMIN_IDS = [7156406347, 8030618244]  # Dusrya admin chi ID ithe taka

ADMIN_USERNAME = "dkman77886"

FREE_CHANNEL_LINK = "https://t.me/+T36niNI2r5xhNmM9"
PREMIUM_CHANNEL_LINK = "https://t.me/+gu10m2ki2zplZTNl"

QR_FILE = "qr.png"
USERS_FILE = "users.json"

bot = telebot.TeleBot(TOKEN)
admin_state = {}

# ---------- USERS ----------
def load_users():
    if not os.path.exists(USERS_FILE):
        return []
    with open(USERS_FILE, "r") as f:
        return json.load(f)

def save_users(users):
    with open(USERS_FILE, "w") as f:
        json.dump(users, f)

def add_user(user):
    users = load_users()
    if not any(u["id"] == user.id for u in users):
        users.append({
            "id": user.id,
            "name": user.first_name,
            "username": user.username if user.username else "NoUsername",
            "premium": False
        })
        save_users(users)

def give_premium(user_id, value=True):
    users = load_users()
    for u in users:
        if u["id"] == user_id:
            u["premium"] = value
    save_users(users)

# ---------- START ----------
@bot.message_handler(commands=['start'])
def start(message):
    add_user(message.from_user)

    markup = InlineKeyboardMarkup()
    markup.add(
        InlineKeyboardButton("🔓 Join Free Channel", url=FREE_CHANNEL_LINK)
    )
    markup.add(
        InlineKeyboardButton("💎 Premium Channel", callback_data="premium")
    )

    bot.send_message(
        message.chat.id,
        "🔥 Welcome to Viral MMS 🔥\n\n"
        "💥 100+ Trending Videos\n"
        "🔥 Full Content Available\n"
        "😈 Premium Quality\n\n"
        "👉 Choose below 👇",
        reply_markup=markup
    )

# ---------- PREMIUM ----------
@bot.callback_query_handler(func=lambda call: call.data == "premium")
def premium(call):
    bot.answer_callback_query(call.id)

    markup = InlineKeyboardMarkup()
    markup.add(
        InlineKeyboardButton("📩 Contact Admin", url=f"https://t.me/{ADMIN_USERNAME}")
    )

    if os.path.exists(QR_FILE):
        with open(QR_FILE, "rb") as photo:
            bot.send_photo(
                call.message.chat.id,
                photo,
                caption="💎 PREMIUM ACCESS\n\n💰 Price: ₹50\n\nScan QR & pay, then send screenshot.",
                reply_markup=markup
            )
    else:
        bot.send_message(call.message.chat.id, "⚠ QR not found")

# ---------- SCREENSHOT ----------
@bot.message_handler(content_types=['photo'])
def screenshot_handler(message):

    user_id = message.from_user.id
    users = load_users()
    user = next((u for u in users if u["id"] == user_id), None)

    if user and user["premium"]:
        bot.send_message(user_id, "✅ Already premium user")
        return

    file_id = message.photo[-1].file_id
    admin_state[user_id] = file_id

    markup = InlineKeyboardMarkup()
    markup.add(
        InlineKeyboardButton("✅ Approve", callback_data=f"approve_{user_id}"),
        InlineKeyboardButton("❌ Reject", callback_data=f"reject_{user_id}")
    )

    for admin_id in ADMIN_IDS:
        bot.send_photo(
            admin_id,
            file_id,
            caption=f"Payment proof from {message.from_user.first_name}",
            reply_markup=markup
        )

    bot.send_message(user_id, "📨 Screenshot received, wait for approval")

# ---------- ADMIN APPROVAL ----------
@bot.callback_query_handler(func=lambda call: call.data.startswith("approve_") or call.data.startswith("reject_"))
def admin_decision(call):

    if call.from_user.id not in ADMIN_IDS:
        return

    action, uid = call.data.split("_")
    uid = int(uid)

    if action == "approve":
        give_premium(uid, True)
        bot.send_message(uid, f"✅ Approved!\nJoin Premium:\n{PREMIUM_CHANNEL_LINK}")
        bot.answer_callback_query(call.id, "Approved")

    else:
        bot.send_message(uid, "❌ Payment Rejected")
        bot.answer_callback_query(call.id, "Rejected")

# ---------- ADMIN PANEL ----------
@bot.message_handler(commands=['admin'])
def admin_panel(message):
    if message.from_user.id not in ADMIN_IDS:
        return

    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("📊 Dashboard", callback_data="dashboard"),
        InlineKeyboardButton("👥 Users", callback_data="users"),
        InlineKeyboardButton("📢 Broadcast", callback_data="broadcast"),
        InlineKeyboardButton("🔍 Search", callback_data="search")
    )

    bot.send_message(message.chat.id, "🎛 Admin Panel", reply_markup=markup)

# ---------- DASHBOARD ----------
@bot.callback_query_handler(func=lambda call: call.data == "dashboard")
def dashboard(call):
    if call.from_user.id not in ADMIN_IDS:
        return

    users = load_users()
    total = len(users)
    premium = len([u for u in users if u["premium"]])
    free = total - premium
    conv = round((premium / total * 100), 2) if total else 0

    bot.send_message(
        call.message.chat.id,
        f"📊 DASHBOARD\n\n"
        f"👥 Users: {total}\n"
        f"💎 Premium: {premium}\n"
        f"🆓 Free: {free}\n"
        f"📈 Conversion: {conv}%"
    )

# ---------- USERS LIST ----------
@bot.callback_query_handler(func=lambda call: call.data == "users")
def users(call):
    if call.from_user.id not in ADMIN_IDS:
        return

    users = load_users()
    text = "👥 USERS LIST\n\n"

    for u in users:
        text += f"{u['id']} | {u['name']} | @{u['username']} | {u['premium']}\n"

    for i in range(0, len(text), 3500):
        bot.send_message(call.message.chat.id, text[i:i+3500])

# ---------- BROADCAST ----------
@bot.callback_query_handler(func=lambda call: call.data == "broadcast")
def broadcast(call):
    if call.from_user.id not in ADMIN_IDS:
        return

    admin_state[call.from_user.id] = "broadcast"
    bot.send_message(call.message.chat.id, "📢 Send text or photo")

# ---------- SEARCH ----------
@bot.callback_query_handler(func=lambda call: call.data == "search")
def search(call):
    if call.from_user.id not in ADMIN_IDS:
        return

    admin_state[call.from_user.id] = "search"
    bot.send_message(call.message.chat.id, "🔍 Send User ID")

# ---------- ADMIN HANDLER ----------
@bot.message_handler(content_types=['text', 'photo'])
def admin_handler(message):

    if message.from_user.id not in ADMIN_IDS:
        return

    state = admin_state.get(message.from_user.id)

    # BROADCAST
    if state == "broadcast":
        users = load_users()

        if message.content_type == "text":
            for u in users:
                try:
                    bot.send_message(u["id"], message.text)
                except:
                    pass

        elif message.content_type == "photo":
            file_id = message.photo[-1].file_id
            caption = message.caption if message.caption else ""

            for u in users:
                try:
                    bot.send_photo(u["id"], file_id, caption=caption)
                except:
                    pass

        bot.send_message(message.chat.id, "✅ Broadcast Done")
        admin_state[message.from_user.id] = None

    # SEARCH
    elif state == "search":
        try:
            uid = int(message.text)
            users = load_users()
            user = next((u for u in users if u["id"] == uid), None)

            if user:
                bot.send_message(
                    message.chat.id,
                    f"👤 USER\n\nID: {user['id']}\nName: {user['name']}\nPremium: {user['premium']}"
                )
            else:
                bot.send_message(message.chat.id, "❌ Not found")
        except:
            bot.send_message(message.chat.id, "❌ Invalid ID")

        admin_state[message.from_user.id] = None

# ---------- RUN ----------
print("🔥 Bot Running...")
bot.infinity_polling()
