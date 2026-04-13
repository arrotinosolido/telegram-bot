import telebot
from telebot import types
import json
import os
import random
import threading
import time

# ================= TOKEN =================
TOKEN = os.getenv("TOKEN")
bot = telebot.TeleBot(TOKEN, parse_mode="HTML")

# ================= CONFIG =================
ADMIN_IDS = [6048916888, 401484954]

CHANNEL = "@plannnnb"
CHANNEL_2 = "@ReVape_bgd"
CHANNEL_3 = "@marselbelgorod"

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
        m1 = bot.get_chat_member(CHANNEL, int(user_id))
        m2 = bot.get_chat_member(CHANNEL_2, int(user_id))
        m3 = bot.get_chat_member(CHANNEL_3, int(user_id))

        return all([
            m1.status in ["member", "creator", "administrator"],
            m2.status in ["member", "creator", "administrator"],
            m3.status in ["member", "creator", "administrator"]
        ])
    except:
        return False

# ================= MENU =================
def main_menu():
    markup = types.InlineKeyboardMarkup()

    markup.add(
        types.InlineKeyboardButton("🎟 Участвовать", callback_data="join"),
        types.InlineKeyboardButton("🎫 Мой билет", callback_data="my_ticket")
    )

    markup.add(
        types.InlineKeyboardButton(
            "💳 Купить билет",
            url="https://69d6a7bcb9e55a51389ed7d2.ticketscloud.org/"
        )
    )

    return markup

# ================= START =================
@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(
        message.chat.id,
        "🎉 <b>Добро пожаловать в розыгрыш!</b>",
        reply_markup=main_menu()
    )

# ================= ADMIN =================
@bot.message_handler(commands=['admin'])
def admin(message):
    if message.from_user.id not in ADMIN_IDS:
        bot.send_message(message.chat.id, "❌ Нет доступа")
        return

    markup = types.InlineKeyboardMarkup(row_width=2)

    markup.add(
        types.InlineKeyboardButton("🏆 Победители", callback_data="admin_winner"),
        types.InlineKeyboardButton("👥 Список", callback_data="admin_list"),
    )

    markup.add(
        types.InlineKeyboardButton("📦 Экспорт", callback_data="admin_export"),
        types.InlineKeyboardButton("🗑 Удалить билет", callback_data="admin_delete"),
    )

    bot.send_message(
        message.chat.id,
        f"👑 <b>Админ панель</b>\n👥 Участников: {len(participants)}",
        reply_markup=markup
    )

# ================= SLOT ANIMATION + 3 WINNERS =================
def run_slot_animation(bot, cid, participants_copy):

    if len(participants_copy) < 3:
        bot.send_message(cid, "❌ Нужно минимум 3 участника")
        return

    users = list(participants_copy.values())
    msg = bot.send_message(cid, "🎰 Запуск розыгрыша...")

    speed = 0.1

    for i in range(20):
        u1 = random.choice(users)
        u2 = random.choice(users)
        u3 = random.choice(users)

        text = (
            "🎰 <b>КРУТИМ...</b>\n\n"
            f"| {u1['username']} |\n"
            f"| {u2['username']} |\n"
            f"| {u3['username']} |"
        )

        try:
            bot.edit_message_text(text, cid, msg.message_id)
        except:
            pass

        time.sleep(speed)
        speed += 0.02

    # 🏆 3 победителя
    winner_ids = random.sample(list(participants_copy.keys()), k=3)
    winners = [participants_copy[w] for w in winner_ids]

    text = "🎉 <b>ПОБЕДИТЕЛИ!</b>\n\n"

    for i, w in enumerate(winners, 1):
        text += (
            f"🏆 {i} место\n"
            f"👤 {w['username']}\n"
            f"🎟 {w['ticket']}\n\n"
        )

    bot.edit_message_text(text, cid, msg.message_id)

    bot.send_message(CHANNEL, text)

# ================= CALLBACK =================
@bot.callback_query_handler(func=lambda call: True)
def callback(call):
    cid = call.message.chat.id
    uid = str(call.from_user.id)

    # JOIN
    if call.data == "join":

        if uid in participants:
            bot.send_message(cid, "❌ Ты уже участвуешь!")
            return

        if not is_subscribed(uid):
            markup = types.InlineKeyboardMarkup()

            markup.add(types.InlineKeyboardButton("📢 Канал 1", url="https://t.me/plannnnb"))
            markup.add(types.InlineKeyboardButton("📢 Канал 2", url="https://t.me/ReVape_bgd"))
            markup.add(types.InlineKeyboardButton("📢 Канал 3", url="https://t.me/marselbelgorod"))

            markup.add(types.InlineKeyboardButton("✅ Я подписался", callback_data="check_sub"))

            bot.send_message(cid, "❌ Подпишись на все 3 канала:", reply_markup=markup)
            return

        waiting_ticket.add(uid)
        bot.send_message(cid, "🎟 Введи номер билета:")

    elif call.data == "check_sub":

        if is_subscribed(uid):
            waiting_ticket.add(uid)
            bot.send_message(cid, "✅ Подписка подтверждена!\n🎟 Введи билет:")
        else:
            bot.send_message(cid, "❌ Ты не подписан!")

    elif call.data == "my_ticket":

        if uid in participants:
            bot.send_message(cid, f"🎫 Твой билет:\n🎟 <code>{participants[uid]['ticket']}</code>")
        else:
            bot.send_message(cid, "❌ Нет билета")

    elif call.data == "admin_winner":

        if call.from_user.id not in ADMIN_IDS:
            return

        threading.Thread(
            target=run_slot_animation,
            args=(bot, cid, participants.copy()),
            daemon=True
        ).start()

    elif call.data == "admin_list":

        if call.from_user.id not in ADMIN_IDS:
            return

        text = "👥 <b>Участники:</b>\n\n"
        for i, data in enumerate(participants.values(), 1):
            text += f"{i}. {data['username']} — {data['ticket']}\n"

        bot.send_message(cid, text)

    elif call.data == "admin_export":

        if call.from_user.id not in ADMIN_IDS:
            return

        file_path = os.path.join(BASE_DIR, "participants_export.txt")

        with open(file_path, "w", encoding="utf-8") as f:
            for data in participants.values():
                f.write(f"{data['username']} | {data['ticket']}\n")

        with open(file_path, "rb") as f:
            bot.send_document(cid, f)

    elif call.data == "admin_delete":

        if call.from_user.id not in ADMIN_IDS:
            return

        waiting_ticket.add(f"delete:{uid}")
        bot.send_message(cid, "✏️ Введи билет для удаления:")

# ================= INPUT =================
@bot.message_handler(func=lambda m: True)
def ticket_input(message):

    uid = str(message.from_user.id)
    text = message.text.strip()

    # DELETE MODE
    if f"delete:{uid}" in waiting_ticket:

        found = None
        for user_id, data in list(participants.items()):
            if data["ticket"] == text:
                found = user_id
                break

        if found:
            del participants[found]
            save_data()
            bot.send_message(message.chat.id, "🗑 Удалено")
        else:
            bot.send_message(message.chat.id, "❌ Не найдено")

        waiting_ticket.discard(f"delete:{uid}")
        return

    # JOIN MODE
    if uid in waiting_ticket:

        if not text.isdigit():
            bot.send_message(message.chat.id, "❌ Только цифры!")
            return

        for u in participants.values():
            if u["ticket"] == text:
                bot.send_message(message.chat.id, "❌ Такой билет уже есть!")
                return

        username = message.from_user.username or message.from_user.first_name

        participants[uid] = {
            "username": username,
            "ticket": text
        }

        waiting_ticket.discard(uid)
        save_data()

        bot.send_message(
            message.chat.id,
            f"✅ <b>Ты участвуешь!</b>\n🎟 <code>{text}</code>",
            reply_markup=main_menu()
        )

        bot.send_message(
            ADMIN_IDS[0],
            f"🎟 Новый участник\n\n"
            f"👤 @{username}\n"
            f"🎫 Билет: {text}"
        )

# ================= RUN =================
while True:
    try:
        bot.infinity_polling(timeout=60, long_polling_timeout=60)
    except Exception as e:
        print("Ошибка:", e)
        time.sleep(5)
