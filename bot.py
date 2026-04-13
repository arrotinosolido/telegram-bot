import telebot
from telebot import types
import json
import os
import random
import time
import threading
from collections import Counter

TOKEN = os.getenv("TOKEN")
ADMIN_IDS = [6048916888, 401484954]
CHANNEL = "@plannnnb"

bot = telebot.TeleBot(TOKEN)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(BASE_DIR, "participants.json")
WINNERS_FILE = os.path.join(BASE_DIR, "winners.json")

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

def save_data():
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(participants, f, ensure_ascii=False, indent=2)

def save_winners():
    with open(WINNERS_FILE, "w", encoding="utf-8") as f:
        json.dump(winners, f, ensure_ascii=False, indent=2)

def is_admin(user_id):
    return user_id in ADMIN_IDS

def is_subscribed(user_id):
    try:
        member = bot.get_chat_member(CHANNEL, user_id)
        return member.status in ["member", "creator", "administrator"]
    except:
        return False

def main_menu():
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("🎟 Участвовать", callback_data="join"),
        types.InlineKeyboardButton("🎫 Мой билет", callback_data="my_ticket")
    )
    return markup

@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, "🎉 Бот розыгрыша", reply_markup=main_menu())

@bot.message_handler(commands=['admin'])
def admin(message):
    if not is_admin(message.from_user.id):
        bot.send_message(message.chat.id, "❌ Нет доступа")
        return
    bot.send_message(message.chat.id, f"👑 Админ
Участников: {len(participants)}")

@bot.callback_query_handler(func=lambda call: True)
def callback(call):
    cid = call.message.chat.id
    uid = call.from_user.id

    if call.data == "join":
        if str(uid) in participants:
            bot.send_message(cid, "❌ Уже участвуешь")
            return

        if not is_subscribed(uid):
            bot.send_message(cid, "❌ Нет подписки")
            return

        waiting_ticket.add(uid)
        bot.send_message(cid, "🎟 Введи билет")

    elif call.data == "my_ticket":
        if str(uid) in participants:
            bot.send_message(cid, participants[str(uid)]["ticket"])
        else:
            bot.send_message(cid, "❌ Нет билета")

@bot.message_handler(func=lambda m: m.from_user.id in waiting_ticket)
def ticket(message):
    uid = str(message.from_user.id)
    participants[uid] = {
        "username": message.from_user.username or "user",
        "ticket": message.text.strip()
    }
    waiting_ticket.discard(message.from_user.id)
    save_data()
    bot.send_message(message.chat.id, "✅ Готово")

def auto_draw():
    while True:
        time.sleep(3600)
        if participants:
            winner = random.choice(list(participants.values()))
            bot.send_message(CHANNEL, f"🏆 {winner['username']} {winner['ticket']}")

threading.Thread(target=auto_draw, daemon=True).start()

bot.infinity_polling(skip_pending=True)
