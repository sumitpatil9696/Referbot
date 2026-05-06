import telebot
from telebot.types import ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton
import json
import os
import sqlite3

TOKEN = "8738920831:AAFRTqzSMA-yihy_xyLLm6nn9EUEvIefdoQ"
ADMIN_ID = 7156406347

bot = telebot.TeleBot(TOKEN)

# ---------------- SQLITE DATABASE ----------------
conn = sqlite3.connect("bot.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    name TEXT,
    balance INTEGER,
    referrals INTEGER
)
""")
conn.commit()

def db_add_user(uid, name):
    cursor.execute("INSERT OR IGNORE INTO users VALUES (?, ?, ?, ?)", (uid, name, 0, 0))
    conn.commit()

def db_update_balance(uid, amount):
    cursor.execute("UPDATE users SET balance = balance + ? WHERE user_id=?", (amount, uid))
    conn.commit()

def db_get_balance(uid):
    cursor.execute("SELECT balance FROM users WHERE user_id=?", (uid,))
    r = cursor.fetchone()
    return r[0] if r else 0

def db_add_ref(uid):
    cursor.execute("UPDATE users SET referrals = referrals + 1 WHERE user_id=?", (uid,))
    conn.commit()

def db_get_ref(uid):
    cursor.execute("SELECT referrals FROM users WHERE user_id=?", (uid,))
    r = cursor.fetchone()
    return r[0] if r else 0

# ---------------- OLD DATABASE (UNCHANGED) ----------------
users = {}
wallet = {}
referrals = {}
pending_withdraw = {}
awaiting_screenshot = {}
broadcast_mode = {}

REF_BONUS = 25
DAILY_BONUS = 10
MIN_WITHDRAW = 125

# ---------------- SAVE SYSTEM ----------------
DATA_FILE = "data.json"

def load_data():
    global users, wallet, referrals, pending_withdraw
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            data = json.load(f)
            users.update({int(k): v for k, v in data.get("users", {}).items()})
            wallet.update({int(k): v for k, v in data.get("wallet", {}).items()})
            referrals.update({int(k): v for k, v in data.get("referrals", {}).items()})
            pending_withdraw.update({int(k): v for k, v in data.get("pending", {}).items()})

def save_data():
    with open(DATA_FILE, "w") as f:
        json.dump({
            "users": users,
            "wallet": wallet,
            "referrals": referrals,
            "pending": pending_withdraw
        }, f)

# ---------------- MENU ----------------
def menu():
    m = ReplyKeyboardMarkup(resize_keyboard=True)
    m.row("💰 Wallet", "🔗 Invite")
    m.row("🎁 Daily Bonus", "🏆 Top Users")
    m.row("💸 Withdraw")
    return m

# ---------------- START ----------------
@bot.message_handler(commands=['start'])
def start(msg):
    uid = msg.from_user.id
    name = msg.from_user.first_name

    # OLD + SQLITE BOTH SAVE
    if uid not in users:
        users[uid] = name
        wallet[uid] = 0
        referrals[uid] = 0
        save_data()

    db_add_user(uid, name)

    args = msg.text.split()

    if len(args) > 1:
        try:
            ref_id = int(args[1])
            if ref_id != uid and ref_id in users:
                wallet[ref_id] += REF_BONUS
                referrals[ref_id] += 1
                db_update_balance(ref_id, REF_BONUS)
                db_add_ref(ref_id)
                save_data()
        except:
            pass

    bot.send_message(uid, f"""
👤 {name}
💰 ₹{wallet[uid]}
👥 {referrals[uid]}
""", reply_markup=menu())

# ---------------- WALLET ----------------
@bot.message_handler(func=lambda m: m.text == "💰 Wallet")
def wallet_view(msg):
    uid = msg.from_user.id
    bot.send_message(uid, f"💰 ₹{wallet.get(uid,0)}")

# ---------------- BONUS ----------------
@bot.message_handler(func=lambda m: m.text == "🎁 Daily Bonus")
def bonus(msg):
    uid = msg.from_user.id
    wallet[uid] += DAILY_BONUS
    db_update_balance(uid, DAILY_BONUS)
    save_data()
    bot.send_message(uid, f"₹{DAILY_BONUS} Added")

# ---------------- ADMIN PANEL ----------------
@bot.message_handler(commands=['panel'])
def panel(msg):
    if msg.from_user.id != ADMIN_ID:
        return

    m = ReplyKeyboardMarkup(resize_keyboard=True)
    m.row("📊 Dashboard", "🔍 Search User")
    m.row("➕ Add Balance", "➖ Deduct Balance")
    m.row("📋 Pending List")

    bot.send_message(msg.chat.id, "Admin Panel", reply_markup=m)

# ---------------- DASHBOARD ----------------
@bot.message_handler(func=lambda m: m.text == "📊 Dashboard")
def dashboard(msg):
    if msg.from_user.id != ADMIN_ID:
        return

    bot.send_message(msg.chat.id, f"""
👥 {len(users)}
💰 ₹{sum(wallet.values())}
⏳ {len(pending_withdraw)}
""")

# ---------------- SEARCH FIX ----------------
@bot.message_handler(func=lambda m: m.text == "🔍 Search User")
def search(msg):
    if msg.from_user.id != ADMIN_ID:
        return
    m = bot.send_message(msg.chat.id, "Send User ID:")
    bot.register_next_step_handler(m, search_process)

def search_process(msg):
    try:
        uid = int(msg.text)

        if uid not in users:
            bot.send_message(msg.chat.id, "User not found")
            return

        bot.send_message(msg.chat.id, f"""
👤 {users[uid]}
💰 ₹{wallet[uid]}
👥 {referrals[uid]}
""")
    except:
        bot.send_message(msg.chat.id, "Invalid ID")

# ---------------- ADD FIX ----------------
@bot.message_handler(func=lambda m: m.text == "➕ Add Balance")
def add(msg):
    if msg.from_user.id != ADMIN_ID:
        return
    m = bot.send_message(msg.chat.id, "user_id amount")
    bot.register_next_step_handler(m, add_process)

def add_process(msg):
    try:
        parts = msg.text.split()
        if len(parts) != 2:
            bot.send_message(msg.chat.id, "Format: id amount")
            return

        uid = int(parts[0])
        amt = int(parts[1])

        if uid not in users:
            bot.send_message(msg.chat.id, "User not found")
            return

        wallet[uid] += amt
        db_update_balance(uid, amt)
        save_data()

        bot.send_message(uid, f"₹{amt} added")
        bot.send_message(msg.chat.id, "Done")
    except:
        bot.send_message(msg.chat.id, "Error")

# ---------------- DEDUCT FIX ----------------
@bot.message_handler(func=lambda m: m.text == "➖ Deduct Balance")
def deduct(msg):
    if msg.from_user.id != ADMIN_ID:
        return
    m = bot.send_message(msg.chat.id, "user_id amount")
    bot.register_next_step_handler(m, deduct_process)

def deduct_process(msg):
    try:
        parts = msg.text.split()
        if len(parts) != 2:
            bot.send_message(msg.chat.id, "Format: id amount")
            return

        uid = int(parts[0])
        amt = int(parts[1])

        if uid not in users:
            bot.send_message(msg.chat.id, "User not found")
            return

        wallet[uid] -= amt
        db_update_balance(uid, -amt)
        save_data()

        bot.send_message(uid, f"₹{amt} deducted")
        bot.send_message(msg.chat.id, "Done")
    except:
        bot.send_message(msg.chat.id, "Error")

# ---------------- PENDING ----------------
@bot.message_handler(func=lambda m: m.text == "📋 Pending List")
def pending_list(msg):
    if msg.from_user.id != ADMIN_ID:
        return

    if not pending_withdraw:
        bot.send_message(msg.chat.id, "No pending")
        return

    text = ""
    for uid, amt in pending_withdraw.items():
        text += f"{uid} → ₹{amt}\n"

    bot.send_message(msg.chat.id, text)

# ---------------- RUN ----------------
load_data()
bot.polling()
