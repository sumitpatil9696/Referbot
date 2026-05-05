import telebot
from telebot.types import ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton

TOKEN = "8738920831:AAFRTqzSMA-yihy_xyLLm6nn9EUEvIefdoQ"
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


# ---------------- MENU (PREMIUM UI) ----------------
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

    if uid not in users:
        users[uid] = name
        wallet[uid] = 0
        referrals[uid] = 0

    args = msg.text.split()

    if len(args) > 1:
        try:
            ref_id = int(args[1])
            if ref_id != uid and ref_id in users:
                wallet[ref_id] += REF_BONUS
                referrals[ref_id] += 1

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

    bot.send_message(uid, f"""
╔═══ 🎁 BONUS CLAIMED ═══╗

💰 +₹{DAILY_BONUS} Added

🔥 Come back daily for more!

╚══════════════════════╝
""")


# ---------------- LEADERBOARD ----------------
@bot.message_handler(func=lambda m: m.text == "🏆 Top Users")
def leaderboard(msg):

    if not referrals:
        bot.send_message(msg.chat.id, "⚠️ No data available yet")
        return

    sorted_users = sorted(referrals.items(), key=lambda x: x[1], reverse=True)

    text = "🏆 TOP EARNERS\n━━━━━━━━━━━━━━━\n\n"

    i = 1
    for uid, ref in sorted_users[:5]:
        name = users.get(uid, "User")
        text += f"{i}. {name} — {ref} invites\n"
        i += 1

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


# ---------------- ADMIN ----------------
@bot.callback_query_handler(func=lambda call: call.from_user.id == ADMIN_ID)
def callback(call):
    data = call.data

    if data.startswith("ap_"):
        uid = int(data.split("_")[1])

        wallet[uid] = 0
        pending_withdraw.pop(uid, None)

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

        bot.send_message(uid, "❌ Withdrawal Rejected")


# ---------------- RUN ----------------
bot.polling()
