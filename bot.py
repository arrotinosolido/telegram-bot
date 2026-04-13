import telebot
from telebot import types
import json
import os
import random

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

# состояния пользователей
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

# ================= ADMIN PANEL =================
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
        f"👑 Админ панель\n👥 Участников: {len(participants)}",
        reply_markup=markup
    )

# ================= CALLBACK =================
@bot.callback_query_handler(func=lambda call: True)
def callback(call):
    cid = call.message.chat.id
    uid = str(call.from_user.id)

    # ================= JOIN =================
    if call.data == "join":

        if uid in participants:
            bot.send_message(cid, "❌ Ты уже участвуешь!")
            return

        if not is_subscribed(uid):
            markup = types.InlineKeyboardMarkup()
            markup.add(
                types.InlineKeyboardButton(
                    "📢 Подписаться",
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

        if uid in participants:
            bot.send_message(
                cid,
                f"🎫 Твой билет:\n🎟 {participants[uid]['ticket']}"
            )
        else:
            bot.send_message(cid, "❌ Ты ещё не участвовал")

    # ================= WINNER =================
    elif call.data == "admin_winner":

        if call.from_user.id not in ADMIN_IDS:
            return

        if not participants:
            bot.send_message(cid, "❌ Нет участников")
            return

        winner_id = random.choice(list(participants.keys()))
        winner = participants[winner_id]

        bot.send_message(
            cid,
            "🎉 РОЗЫГРЫШ!\n\n"
            f"🏆 Победитель:\n"
            f"👤 {winner['username']}\n"
            f"🎟 {winner['ticket']}"
        )

    # ================= LIST =================
    elif call.data == "admin_list":

        if call.from_user.id not in ADMIN_IDS:
            return

        if not participants:
            bot.send_message(cid, "❌ Пусто")
            return

        text = "👥 Участники:\n\n"
        for i, (uid_p, data) in enumerate(participants.items(), 1):
            text += f"{i}. {data['username']} — {data['ticket']}\n"

        bot.send_message(cid, text)

    # ================= EXPORT =================
    elif call.data == "admin_export":

        if call.from_user.id not in ADMIN_IDS:
            return

        file_path = os.path.join(BASE_DIR, "participants_export.txt")

        with open(file_path, "w", encoding="utf-8") as f:
            for uid_p, data in participants.items():
                f.write(f"{data['username']} | {data['ticket']}\n")

        with open(file_path, "rb") as f:
            bot.send_document(cid, f)

    # ================= DELETE MODE =================
    elif call.data == "admin_delete":

        if call.from_user.id not in ADMIN_IDS:
            return

        waiting_ticket.add(f"delete:{uid}")
        bot.send_message(cid, "✏️ Отправь номер билета для удаления:")

# ================= TICKET INPUT =================
@bot.message_handler(func=lambda m: True)
def ticket_input(message):

    uid = str(message.from_user.id)
    text = message.text.strip()

    # ================= DELETE MODE =================
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

    # ================= JOIN MODE =================
    if uid in waiting_ticket:

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
            f"✅ Ты участвуешь!\n🎟 {text}",
            reply_markup=main_menu()
        )

# ================= RUN =================
bot.infinity_polling()
