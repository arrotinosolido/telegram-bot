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
        member = bot.get_chat_member(CHANNEL, int(user_id))
        return member.status in ["member", "creator", "administrator"]
    except:
        return False

# ================= MENU =================
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
        types.InlineKeyboardButton("🏆 Победитель", callback_data="admin_winner"),
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

# ================= 🎰 SLOT ANIMATION =================
def run_slot_animation(bot, cid, participants_copy):

    users = list(participants_copy.values())

    msg = bot.send_message(cid, "🎰 Запуск слотов...")

    if len(users) < 1:
        bot.edit_message_text("❌ Нет участников", cid, msg.message_id)
        return

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

    # почти выиграл
    almost = random.choice(users)

    bot.edit_message_text(
        f"😱 <b>ПОЧТИ!!!</b>\n\n"
        f"| {almost['username']} |\n"
        f"| {almost['username']} |\n"
        f"| ??? |",
        cid,
        msg.message_id
    )

    time.sleep(1)

    # победитель
    winner_id = random.choice(list(participants_copy.keys()))
    winner = participants_copy[winner_id]

    bot.edit_message_text(
        f"🎉 <b>ДЖЕКПОТ!!!</b>\n\n"
        f"🏆 Победитель:\n"
        f"👤 {winner['username']}\n"
        f"🎟 <code>{winner['ticket']}</code>",
        cid,
        msg.message_id
    )

    # отправка в канал
    try:
        bot.send_message(
            CHANNEL,
            f"🏆 <b>Победитель розыгрыша</b>\n\n"
            f"👤 {winner['username']}\n"
            f"🎟 <code>{winner['ticket']}</code>"
        )
    except:
        pass

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
            markup.add(
                types.InlineKeyboardButton("📢 Подписаться", url="https://t.me/plannnnb")
            )
            markup.add(
                types.InlineKeyboardButton("✅ Я подписался", callback_data="check_sub")
            )

            bot.send_message(
                cid,
                "❌ Подпишись на канал для участия:",
                reply_markup=markup
            )
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
            bot.send_message(
                cid,
                f"🎫 Твой билет:\n🎟 <code>{participants[uid]['ticket']}</code>"
            )
        else:
            bot.send_message(cid, "❌ Нет билета")

    # WINNER
    elif call.data == "admin_winner":

        if call.from_user.id not in ADMIN_IDS:
            return

        if not participants:
            bot.send_message(cid, "❌ Нет участников")
            return

        threading.Thread(
            target=run_slot_animation,
            args=(bot, cid, participants.copy()),
            daemon=True
        ).start()

    # LIST
    elif call.data == "admin_list":

        if call.from_user.id not in ADMIN_IDS:
            return

        text = "👥 <b>Участники:</b>\n\n"
        for i, data in enumerate(participants.values(), 1):
            text += f"{i}. {data['username']} — {data['ticket']}\n"

        bot.send_message(cid, text)

    # EXPORT
    elif call.data == "admin_export":

        if call.from_user.id not in ADMIN_IDS:
            return

        file_path = os.path.join(BASE_DIR, "participants_export.txt")

        with open(file_path, "w", encoding="utf-8") as f:
            for data in participants.values():
                f.write(f"{data['username']} | {data['ticket']}\n")

        with open(file_path, "rb") as f:
            bot.send_document(cid, f)

    # DELETE
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

# ================= RUN =================
bot.infinity_polling()
