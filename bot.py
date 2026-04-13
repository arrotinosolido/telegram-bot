import telebot
from telebot import types
import json
import os
import random
import time

# ================= TOKEN =================
TOKEN = os.getenv("TOKEN")

bot = telebot.TeleBot(TOKEN)

# ================= CONFIG =================
ADMIN_IDS = [6048916888, 401484954]
CHANNEL = "@plannnnb"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(BASE_DIR, "participants.json")

# ================= DATA =================
if os.path.exists(DATA_FILE):
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        participants = json.load(f)
else:
    participants = {}

waiting_ticket = set()

# ================= SAVE =================
def save_data():
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(participants, f, ensure_ascii=False, indent=2)

# ================= CHECK SUB =================
def is_subscribed(user_id):
    try:
        member = bot.get_chat_member(CHANNEL, user_id)
        return member.status in ["member", "creator", "administrator"]
    except:
        return False

# ================= MAIN MENU =================
def main_menu():
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("🎟 Участвовать", callback_data="join"),
        types.InlineKeyboardButton("🎫 Мой билет", callback_data="my_ticket")
    )
    return markup

# ================= START =================
@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(
        message.chat.id,
        "🎉 Добро пожаловать в розыгрыш!",
        reply_markup=main_menu()
    )

# ================= ADMIN =================
@bot.message_handler(commands=['admin'])
def admin(message):
    if message.from_user.id not in ADMIN_IDS:
        bot.send_message(message.chat.id, "❌ Нет доступа")
        return

    bot.send_message(
        message.chat.id,
        f"👑 Админ панель\n👥 Участников: {len(participants)}"
    )

# ================= CALLBACK =================
@bot.callback_query_handler(func=lambda call: True)
def callback(call):
    cid = call.message.chat.id
    uid = call.from_user.id

    # ================= JOIN =================
    if call.data == "join":

        if str(uid) in participants:
            bot.send_message(cid, "❌ Ты уже участвуешь!")
            return

        if not is_subscribed(uid):

            markup = types.InlineKeyboardMarkup()

            markup.add(
                types.InlineKeyboardButton(
                    "📢 Подписаться на канал",
                    url="https://t.me/plannnnb"
                )
            )

            markup.add(
                types.InlineKeyboardButton(
                    "✅ Я подписался",
                    callback_data="check_sub"
                )
            )

            bot.send_message(
                cid,
                "❌ Чтобы участвовать, подпишись на канал:",
                reply_markup=markup
            )
            return

        waiting_ticket.add(uid)
        bot.send_message(cid, "🎟 Введи номер билета:")

    # ================= CHECK SUB =================
    elif call.data == "check_sub":

        if is_subscribed(uid):
            waiting_ticket.add(uid)
            bot.send_message(cid, "✅ Подписка подтверждена!\n🎟 Введи номер билета:")
        else:
            bot.send_message(cid, "❌ Ты ещё не подписан!")

    # ================= MY TICKET =================
    elif call.data == "my_ticket":

        if str(uid) in participants:
            bot.send_message(
                cid,
                f"🎫 Твой билет:\n🎟 {participants[str(uid)]['ticket']}"
            )
        else:
            bot.send_message(cid, "❌ Ты ещё не участвовал")

    # ================= ADMIN WINNER =================
    elif call.data == "admin_winner":

        if uid not in ADMIN_IDS:
            return

        if not participants:
            bot.send_message(cid, "❌ Нет участников")
            return

        winner_id = random.choice(list(participants.keys()))
        winner = participants[winner_id]

        text = (
            "🎉 РОЗЫГРЫШ!\n\n"
            "🏆 Победитель:\n"
            f"👤 {winner['username']}\n"
            f"🎟 {winner['ticket']}"
        )

        bot.send_message(cid, text)

# ================= TICKET INPUT =================
@bot.message_handler(func=lambda m: m.from_user.id in waiting_ticket)
def ticket_input(message):

    uid = str(message.from_user.id)
    ticket = message.text.strip()

    # duplicate check
    for u in participants.values():
        if u["ticket"] == ticket:
            bot.send_message(message.chat.id, "❌ Такой билет уже есть!")
            return

    username = message.from_user.username or message.from_user.first_name

    participants[uid] = {
        "username": username,
        "ticket": ticket
    }

    waiting_ticket.discard(message.from_user.id)
    save_data()

    bot.send_message(
        message.chat.id,
        f"✅ Ты участвуешь!\n🎟 {ticket}",
        reply_markup=main_menu()
    )

# ================= RUN =================
print("Bot started 🚀")
bot.infinity_polling(skip_pending=True)
