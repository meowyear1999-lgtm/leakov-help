import telebot
import sqlite3
import time
import random
import re
import threading
import os

# Берем токен из настроек хостинга
TOKEN = os.getenv("8285689411:AAGCYHrrqnATcAVqhMFeiaB3gLtpLLwVlLk")
bot = telebot.TeleBot(TOKEN)
BOT_NAME = "Leakov Help"

# База данных
db_lock = threading.Lock()
db = sqlite3.connect("leakov.db", check_same_thread=False)
sql = db.cursor()

with db_lock:
    sql.execute("""CREATE TABLE IF NOT EXISTS users (
        chat_id INTEGER, user_id INTEGER, name TEXT, 
        rep INTEGER DEFAULT 0, balance INTEGER DEFAULT 500, 
        warns INTEGER DEFAULT 0, PRIMARY KEY (chat_id, user_id))""")
    db.commit()

def get_user(chat_id, user_id, name="Странник"):
    with db_lock:
        sql.execute("SELECT rep, balance, warns FROM users WHERE chat_id=? AND user_id=?", (chat_id, user_id))
        res = sql.fetchone()
        if not res:
            sql.execute("INSERT INTO users (chat_id, user_id, name) VALUES (?, ?, ?)", (chat_id, user_id, name))
            db.commit()
            return (0, 500, 0)
        return res

def is_admin(chat_id, user_id):
    try:
        member = bot.get_chat_member(chat_id, user_id)
        return member.status in ['creator', 'administrator']
    except: return False

@bot.message_handler(content_types=['text'])
def handle_commands(m):
    if m.chat.type == "private": return
    uid, cid, name, txt = m.from_user.id, m.chat.id, m.from_user.first_name, m.text.lower().strip()
    get_user(cid, uid, name)

    if txt == "профиль":
        rep, bal, warns = get_user(cid, uid)
        bot.reply_to(m, f"👤 {name}\n🌟 Карма: {rep}\n💰 Деньги: {bal}\n⚠️ Варны: {warns}/3")

    elif txt.startswith(('бан', 'кик', 'мут', 'варн')):
        if not is_admin(cid, uid) or not m.reply_to_message: return
        target = m.reply_to_message.from_user
        if txt == 'бан': bot.ban_chat_member(cid, target.id); bot.reply_to(m, f"🔨 {target.first_name} забанен.")
        elif txt == 'кик': bot.ban_chat_member(cid, target.id); bot.unban_chat_member(cid, target.id); bot.reply_to(m, f"👢 {target.first_name} кикнут.")

    elif m.reply_to_message and txt in ['+', 'респект']:
        if m.reply_to_message.from_user.id == uid: return
        with db_lock:
            sql.execute("UPDATE users SET rep = rep + 1 WHERE chat_id=? AND user_id=?", (cid, m.reply_to_message.from_user.id))
            db.commit()
        bot.reply_to(m, "🌟 Репутация повышена!")

    # РП команды
    rp = {"обнять": "🤗 {u} обнял {t}", "ударить": "💥 {u} ударил {t}"}
    if txt in rp and m.reply_to_message:
        bot.reply_to(m, rp[txt].format(u=name, t=m.reply_to_message.from_user.first_name))

print(f"🚀 {BOT_NAME} запущен!")
bot.infinity_polling()
