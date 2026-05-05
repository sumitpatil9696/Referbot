import telebot
from telebot.types import ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton
import json
import os

TOKEN = "7681863270:AAHpNLYx6OSiyPzBleM6AnIiS1K7kFER1EU"
ADMIN_ID = 7156406347

bot = telebot.TeleBot(TOKEN)

# ---------------- DATABASE ----------------
users = {}
wallet = {}
referrals = {}
pending_withdraw = {}
awaiting_screenshot = {}
broadcast_mode = {}

REF_BONUS = 25
DAILY_BONUS = 10
MIN_WITHDRAW = 125

# ---------------- DATA SAVE SYSTEM ----------------
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
    data = {
        "users": users,
        "wallet": wallet,
        "referrals": referrals,
        "pending": pending_withdraw
    }
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)

# ---------------- MENU ----------------
def menu():
    m = ReplyKeyboardMarkup(resize_keyboard=True)
    m.row("💰 Wallet", "🔗 Invite")
    m.row("🎁 Daily Bonus", "🏆 Top Users")
    m.row("💸 Withdraw")
    return m

# ---------------- ADMIN PANEL ----------------
def admin_menu():
    m = ReplyKeyboardMarkup(resize_keyboard=True)
    m.row("👥 Total Users", "📈 Full Stats")
    m.row("💰 Total Balance", "📢 Broadcast")
    return m

@bot.message_handler(commands=['admin'])
def admin_panel(msg):
    if msg.from_user.id != ADMIN_ID:
        return
    bot.send_message(msg.chat.id, "🔐 Admin Panel", reply_markup=admin_menu())

@bot.message_handler(func=lambda m: m.text == "👥 Total Users")
def total_users(msg):
    if msg.from_user.id != ADMIN_ID:
        return
    bot.send_message(msg.chat.id, f"👥 Total Users: {len(users)}")

@bot.message_handler(func=lambda m: m.text == "💰 Total Balance")
def total_balance(msg):
    if msg.from_user.id != ADMIN_ID:
        return
    bot.send_message(msg.chat.id, f"💰 Total Balance: ₹{sum(wallet.values())}")

@bot.message_handler(func=lambda m: m.text == "📈 Full Stats")
def full_stats(msg):
    if msg.from_user.id != ADMIN_ID:
        return

    text = f"""
📊 FULL STATS
━━━━━━━━━━━━━━━
👥 Total Users: {len(users)}
💰 Total Balance: ₹{sum(wallet.values())}
🧾 Pending Withdraw: {len(pending_withdraw)}
━━━━━━━━━━━━━━━
"""
    bot.send_message(msg.chat.id, text)

@bot.message_handler(func=lambda m: m.text == "📢 Broadcast")
def broadcast_start(msg):
    if msg.from_user.id != ADMIN_ID:
        return

    broadcast_mode[msg.from_user.id] = True
    bot.send_message(msg.chat.id, "📢 Send message to broadcast")

@bot.message_handler(func=lambda m: m.from_user.id in broadcast_mode)
def broadcast_send(msg):
    if msg.from_user.id != ADMIN_ID:
        return

    broadcast_mode.pop(msg.from_user.id)

    count = 0
    for uid in users:
        try:
            bot.forward_message(uid, msg.chat.id, msg.message_id)
            count += 1
        except:
            pass

    bot.send_message(msg.chat.id, f"✅ Broadcast sent to {count} users")

# ---------------- START ----------------
@bot.message_handler(commands=['start'])
def start(msg):
    uid = msg.from_user.id
    name = msg.from_user.first_name

    if uid not in users:
        users[uid] = name
        wallet[uid] = 0
        referrals[uid] = 0
        save_data()

    args = msg.text.split()

    if len(args) > 1:
        try:
            ref_id = int(args[1])
            if ref_id != uid and ref_id in users:
                wallet[ref_id] += REF_BONUS
                referrals[ref_id] += 1
                save_data()

                bot.send_message(ref_id, f"""
╭━━━〔 🎉 REFERRAL BONUS 〕━━━╮
┃ 💰 Earned: ₹{REF_BONUS}
┃ 👥 New Invite Joined
╰━━━━━━━━━━━━━━━━━━━━╯
🔥 Keep sharing & earning!
""")
        except:
            pass

    bot.send_message(uid, f"""
╔══════════════════════╗
║      💎 SUMO EARN     ║
╚══════════════════════╝

👤 User: {name}

━━━━━━━━━━━━━━━━━━
💰 Balance: ₹{wallet[uid]}
👥 Referrals: {referrals[uid]}
━━━━━━━━━━━━━━━━━━

🚀 Start earning instantly!
""", reply_markup=menu())

# ---------------- WALLET ----------------
@bot.message_handler(func=lambda m: m.text == "💰 Wallet")
def wallet_view(msg):
    uid = msg.from_user.id

    bot.send_message(uid, f"""
╔═══ 💳 WALLET PANEL ═══╗

💰 Current Balance
➤ ₹{wallet.get(uid,0)}

👥 Total Referrals
➤ {referrals.get(uid,0)}

╚══════════════════════╝
""")

# ---------------- REF LINK ----------------
@bot.message_handler(func=lambda m: m.text == "🔗 Invite")
def ref_link(msg):
    uid = msg.from_user.id
    link = f"https://t.me/{bot.get_me().username}?start={uid}"

    bot.send_message(uid, f"""
╔═══ 🔗 INVITE & EARN ═══╗

📨 Your Referral Link:
{link}

💸 Earn ₹{REF_BONUS} per user

╚══════════════════════╝
""")

# ---------------- BONUS ----------------
@bot.message_handler(func=lambda m: m.text == "🎁 Daily Bonus")
def bonus(msg):
    uid = msg.from_user.id
    wallet[uid] += DAILY_BONUS
    save_data()

    bot.send_message(uid, f"""
╔═══ 🎁 BONUS CLAIMED ═══╗

💰 +₹{DAILY_BONUS} Added

🔥 Come back daily for more!

╚══════════════════════╝
""")

# ---------------- LEADERBOARD ----------------
@bot.message_handler(func=lambda m: m.text == "🏆 Top Users")
def leaderboard(msg):

    text = """🏆 TOP USERS
━━━━━━━━━━━━━━━

👥 Total Users : 2000
💸 Total Money Spent : ₹52350

━━━━━━━━━━━━━━━
📊 Leaderboard
━━━━━━━━━━━━━━━

1. Shreeram : 56 invite
2. Yashvant : 50 invite
3. Suyog : 45 invite
4. Pranav : 30 invite
5. Siddharth : 20 invite
"""

    bot.send_message(msg.chat.id, text)

# ---------------- WITHDRAW ----------------
@bot.message_handler(func=lambda m: m.text == "💸 Withdraw")
def withdraw(msg):
    uid = msg.from_user.id
    bal = wallet.get(uid, 0)

    if bal < MIN_WITHDRAW:
        bot.send_message(uid, f"""
❌ Withdrawal Failed

Minimum: ₹{MIN_WITHDRAW}
Your Balance: ₹{bal}
""")
        return

    pending_withdraw[uid] = bal
    awaiting_screenshot[uid] = True
    save_data()

    bot.send_message(uid, f"""
╔═══ 💸 WITHDRAW REQUEST ═══╗

💰 Amount: ₹{bal}
📌 Processing Fee: ₹25

📲 Scan QR & pay
📸 Send screenshot after payment

╚══════════════════════════╝
""")

    try:
        with open("qr.png", "rb") as qr:
            bot.send_photo(uid, qr)
    except:
        bot.send_message(uid, "⚠️ QR not found")

# ---------------- SCREENSHOT ----------------
@bot.message_handler(content_types=['photo'])
def screenshot(msg):
    uid = msg.from_user.id

    if uid in awaiting_screenshot:
        awaiting_screenshot.pop(uid)

        bot.forward_message(ADMIN_ID, msg.chat.id, msg.message_id)

        kb = InlineKeyboardMarkup()
        kb.add(
            InlineKeyboardButton("✅ Approve", callback_data=f"ap_{uid}"),
            InlineKeyboardButton("❌ Reject", callback_data=f"re_{uid}")
        )

        bot.send_message(ADMIN_ID, f"""
💼 Withdrawal Request

👤 User: {users.get(uid)}
💰 Amount: ₹{pending_withdraw.get(uid,0)}
""", reply_markup=kb)

        bot.send_message(uid, "⏳ Request under review...")

# ---------------- ADMIN APPROVAL ----------------
@bot.callback_query_handler(func=lambda call: call.from_user.id == ADMIN_ID)
def callback(call):
    data = call.data

    if data.startswith("ap_"):
        uid = int(data.split("_")[1])

        wallet[uid] = 0
        pending_withdraw.pop(uid, None)
        save_data()

        kb = InlineKeyboardMarkup()
        kb.add(InlineKeyboardButton("📩 Contact Admin", url="https://t.me/Taskman96"))

        bot.send_message(uid, """
🎉 Withdrawal Approved

📩 Send:
Name
UPI ID
""", reply_markup=kb)

    elif data.startswith("re_"):
        uid = int(data.split("_")[1])

        pending_withdraw.pop(uid, None)
        save_data()

        bot.send_message(uid, "❌ Withdrawal Rejected")

# ---------------- RUN ----------------
load_data()
bot.polling()
