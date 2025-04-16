import requests
import random
import string
import time
from threading import Thread
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

# CONFIGURATION
API_KEY = "_BEMTA6aXO94WhJN9kpqXVh6u99PtD86"
SERVICE_ID = "1425"
SMM_API_URL = "https://panel.smmflw.com/api/v2"
BOT_TOKEN = "1782260566:AAE9d-XBGLE5rlujTVIed4WB-rmDkK169vk"
ALLOWED_USER_ID = 1131172138

user_data = {}

def random_suffix(length=6):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

def modify_link(link):
    if "igsh=" in link:
        base, igsh = link.split("igsh=", 1)
        igsh_core = igsh.split('=')[0]
        return f"{base}igsh={igsh_core}={random_suffix()}"
    else:
        return f"{link}?igsh={random_suffix()}"

def place_order(link, quantity):
    data = {
        'key': API_KEY,
        'action': 'add',
        'service': SERVICE_ID,
        'link': link,
        'quantity': quantity
    }
    try:
        print("[DEBUG] Sending order with:", data)
        response = requests.post(SMM_API_URL, data=data)
        print("[DEBUG] API Response:", response.text)
        return response.json()
    except Exception as e:
        print("[ERROR]", e)
        return {"error": str(e)}

def run_order_loop(chat_id, link, quantity, context):
    while True:
        mod_link = modify_link(link)
        result = place_order(mod_link, quantity)
        if 'order' in result:
            context.bot.send_message(chat_id, f"Order Placed! ID: {result['order']}")
        elif 'error' in result:
            context.bot.send_message(chat_id, f"Error: {result['error']}")
        time.sleep(10)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ALLOWED_USER_ID:
        await update.message.reply_text("Unauthorized access.")
        return
    await update.message.reply_text("Send me the Instagram Reels link.")
    user_data[update.effective_user.id] = {"stage": "waiting_for_link"}

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if uid != ALLOWED_USER_ID:
        await update.message.reply_text("Unauthorized.")
        return

    msg = update.message.text.strip()

    if uid in user_data:
        stage = user_data[uid].get("stage")

        if stage == "waiting_for_link":
            user_data[uid]["link"] = msg
            user_data[uid]["stage"] = "waiting_for_quantity"
            await update.message.reply_text("Now enter the quantity of likes.")

        elif stage == "waiting_for_quantity":
            if msg.isdigit():
                user_data[uid]["quantity"] = int(msg)
                await update.message.reply_text("Starting to place repeated orders...")

                # Start loop in a separate thread
                Thread(target=run_order_loop, args=(uid, user_data[uid]["link"], user_data[uid]["quantity"], context)).start()
                user_data[uid]["stage"] = "running"
            else:
                await update.message.reply_text("Please enter a valid number.")
        elif stage == "running":
            await update.message.reply_text("Already running. Send /start to reset.")
    else:
        await update.message.reply_text("Send /start to begin.")

if __name__ == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("[+] Bot is running...")
    app.run_polling()
