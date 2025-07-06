import os
import json
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)

BOT_TOKEN = os.getenv("BOT_TOKEN")
DATA_FILE = "user_data.json"
QUEUE_FILE = "queue.json"

users = {}
queue = []

def load_data():
    global users, queue
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            users = json.load(f)
    if os.path.exists(QUEUE_FILE):
        with open(QUEUE_FILE, "r") as f:
            queue = json.load(f)

def save_data():
    with open(DATA_FILE, "w") as f:
        json.dump(users, f, indent=4)
    with open(QUEUE_FILE, "w") as f:
        json.dump(queue, f, indent=4)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    load_data()
    user = update.effective_user
    user_id = str(user.id)
    args = context.args

    if user_id not in users:
        users[user_id] = {
            "points": 0,
            "referrals": [],
            "is_vip": False,
            "chat": None
        }
        if args:
            ref_id = args[0]
            if ref_id != user_id and ref_id in users:
                users[ref_id]["points"] += 1
                users[ref_id]["referrals"].append(user_id)
                await context.bot.send_message(chat_id=ref_id, text="🎉 You got 1 point from a referral!")
        await update.message.reply_text("👋 Welcome to Ethio Date Bot!\nUse /match to find someone to chat with.")
    else:
        await update.message.reply_text("👋 Welcome back!\nUse /match to find someone to chat with.")
    save_data()

async def referral(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    bot_name = (await context.bot.get_me()).username
    link = f"https://t.me/{bot_name}?start={user_id}"
    await update.message.reply_text(f"🔗 Your referral link:\n{link}")

async def points(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    pts = users.get(user_id, {}).get("points", 0)
    await update.message.reply_text(f"💰 You have {pts} point(s).")

async def vip(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    if users.get(user_id, {}).get("is_vip"):
        await update.message.reply_text("✅ You are a VIP!")
    else:
        await update.message.reply_text("🚫 You are not a VIP.\nTo upgrade, contact: https://t.me/Mydyds")

async def donate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = "🙏 Support the project:\n\n" \
          "💵 USDT (BEP20): `0xD053b768934b687dbf61697AB1198966A46B06A7`\n\n" \
          "Thank you for your support!"
    await update.message.reply_text(msg, parse_mode="Markdown")

async def match(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    if users[user_id]["chat"]:
        await update.message.reply_text("⚠️ You're already in a chat. Use /end to leave.")
        return

    if queue and queue[0] != user_id:
        partner_id = queue.pop(0)
        users[user_id]["chat"] = partner_id
        users[partner_id]["chat"] = user_id
        await context.bot.send_message(chat_id=user_id, text="✅ Matched! Say hi!")
        await context.bot.send_message(chat_id=partner_id, text="✅ Matched! Say hi!")
    else:
        if user_id not in queue:
            queue.append(user_id)
            await update.message.reply_text("🔍 Searching for a match...")
    save_data()

async def end(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    partner_id = users.get(user_id, {}).get("chat")
    if partner_id:
        users[user_id]["chat"] = None
        users[partner_id]["chat"] = None
        await context.bot.send_message(chat_id=partner_id, text="❌ Your partner has left the chat.")
        await update.message.reply_text("❌ You left the chat.")
    else:
        await update.message.reply_text("❌ You're not in a chat.")
    save_data()

async def chat_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    partner_id = users.get(user_id, {}).get("chat")
    if partner_id:
        await context.bot.send_message(chat_id=partner_id, text=update.message.text)
        users[user_id]["points"] += 1
        save_data()
    else:
        await update.message.reply_text("ℹ️ You're not in a chat. Use /match to find a partner.")

def main():
    load_data()
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("referral", referral))
    app.add_handler(CommandHandler("points", points))
    app.add_handler(CommandHandler("vip", vip))
    app.add_handler(CommandHandler("donate", donate))
    app.add_handler(CommandHandler("match", match))
    app.add_handler(CommandHandler("end", end))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat_handler))

    print("Bot running...")
    app.run_polling()

if __name__ == "__main__":
    main()
