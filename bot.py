import telebot
from telebot import types
import json
import os
import random
import time
import threading
from collections import Counter

# ================= CONFIG =================
TOKEN = os.getenv("TOKEN")

ADMIN_IDS = [6048916888, 401484954]
CHANNEL = "@plannnnb"

bot = telebot.TeleBot(TOKEN)

# ================= FILES =================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(BASE_DIR, "participants.json")
WINNERS_FILE = os.path.join(BASE_DIR, "winners.json")

# ================= DATA LOAD =================
if os.path.exists(DATA_FILE):
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        participants = json.load(f)
else:
    participants = {}

if os.path.exists(WINNERS_FILE):
    with open(WINNERS_FILE, "r", encoding="utf-8") as f:
        winners = json.load(f)
else:
    winners = []

waiting_ticket = set()
last_action = {}

# ================= SAVE =================
def save_data():
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(participants, f, ensure_ascii=False, indent=2)

def save_winners():
    with open(WINNERS_FILE, "w", encoding="utf-8") as f:
        json.dump(winners, f, ensure_ascii=False, indent=2)

# ================= CHECKS =================
def is_admin(user_id):
    return user_id in ADMIN_IDS

def is_subscribed(user_id):
    try:
        member = bot.get_chat_member(CHANNEL, user_id)
        return member.status in ["member", "creator", "administrator"]
    except:
        return False

# ================= MENUS =================
def main_menu():
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("🎟 Участвовать", callback_data="join"),
        types.InlineKeyboardButton("🎫 Мой билет", callback_data="my_ticket")
    )
    markup.add(
        types.InlineKeyboardButton("❓ Правила", callback_data="rules")
    )
    return markup

def admin_menu():
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("📊 Статистика", callback_data="admin_stats"),
        types.InlineKeyboardButton("📋 Участники", callback_data="admin_list")
    )
    markup.add(
        types.InlineKeyboardButton("🎰 Розыгрыш", callback_data="admin_winner"),
        types.InlineKeyboardButton("🧹 Очистка", callback_data="admin_clear")
    )
    markup.add(
        types.InlineKeyboardButton("🔥 Топ", callback_data="admin_top")
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
    if not is_admin(message.from_user.id):
        bot.send_message(message.chat.id, "❌ Нет доступа")
        return

    bot.send_message(
        message.chat.id,
        f"👑 Админ панель\n\n👥 Участников: {len(participants)}",
        reply_markup=admin_menu()
    )

# ================= CALLBACK =================
@bot.callback_query_handler(func=lambda call: True)
def callback(call):
    cid = call.message.chat.id
    uid = call.from_user.id

    # anti spam
    if uid in last_action and time.time() - last_action[uid] < 1:
        return
    last_action[uid] = time.time()

    # JOIN
    if call.data == "join":

        if str(uid) in participants:
            bot.send_message(cid, "❌ Ты уже участвуешь!")
            return

        if not is_subscribed(uid):
            bot.send_message(cid, "❌ Подпишись на канал")
            return

        waiting_ticket.add(uid)
        bot.send_message(cid, "🎟 Введи номер билета:")

    # MY TICKET
    elif call.data == "my_ticket":
        if str(uid) in participants:
            bot.send_message(cid, f"🎟 {participants[str(uid)]['ticket']}")
        else:
            bot.send_message(cid, "❌ Нет билета")

    # RULES
    elif call.data == "rules":
        bot.send_message(
            cid,
            "📜 Правила:\n\n"
            "1. Подписка обязательна\n"
            "2. Один билет = один участник\n"
            "3. Победитель выбирается случайно"
        )

    # ADMIN ONLY
    if not is_admin(uid):
        return

    if call.data == "admin_stats":
        bot.send_message(cid, f"📊 Участников: {len(participants)}")

    elif call.data == "admin_list":
        if not participants:
            bot.send_message(cid, "📭 Пусто")
            return

        text = "📋 Участники:\n\n"
        for u in participants.values():
            text += f"👤 {u['username']} — 🎟 {u['ticket']}\n"

        bot.send_message(cid, text)

    elif call.data == "admin_clear":
        participants.clear()
        save_data()
        bot.send_message(cid, "🧹 База очищена")

    elif call.data == "admin_top":
        tickets = [u["ticket"] for u in participants.values()]
        top = Counter(tickets).most_common(5)

        text = "🔥 Топ билетов:\n\n"
        for t, c in top:
            text += f"{t} — {c} раз\n"

        bot.send_message(cid, text)

    elif call.data == "admin_winner":

        if not participants:
            bot.send_message(cid, "❌ Нет участников")
            return

        winner_id = random.choice(list(participants.keys()))
        winner = participants[winner_id]

        result = (
            "🎉 Результаты!\n\n"
            "🏆 Победитель:\n"
            f"{winner['username']}\n"
            f"🎟 {winner['ticket']}"
        )

        winners.append(winner)
        save_winners()

        bot.send_message(cid, result)
        bot.send_message(CHANNEL, result)

# ================= TICKET INPUT =================
@bot.message_handler(func=lambda m: m.from_user.id in waiting_ticket)
def get_ticket(message):
    uid = str(message.from_user.id)
    ticket = message.text.strip()

    if uid in participants:
        bot.send_message(message.chat.id, "❌ Ты уже участвуешь!")
        waiting_ticket.discard(message.from_user.id)
        return

    for u in participants.values():
        if u["ticket"] == ticket:
            bot.send_message(message.chat.id, "❌ Такой билет уже есть")
            return

    username = message.from_user.username or message.from_user.first_name

    participants[uid] = {
        "username": username,
        "ticket": ticket
    }

    waiting_ticket.discard(message.from_user.id)
    save_data()

    bot.send_message(message.chat.id, "✅ Ты участвуешь!")

# ================= RUN =================
print("Bot started 🚀")
bot.infinity_polling(skip_pending=True)
