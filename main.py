import json
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, CallbackQueryHandler, filters, ContextTypes

# ===== KEEP ALIVE =====
from flask import Flask
from threading import Thread

web = Flask('')

@web.route('/')
def home():
    return "Bot Running 24/7"

def run():
    web.run(host='0.0.0.0', port=8080)

def keep_alive():
    Thread(target=run).start()

# ===== CONFIG =====
TOKEN = "8502098422:AAHFtNfJEFAirvzvBrVOCoLqPKvmHHicDQ8"
ADMIN_ID = 6766447756
CHANNEL = "@ST_WHATAPPS_CHEKAR"
SUPPORT = "@SHANTO_VAI_OWNER_TX"
LOGO_URL = "https://i.imgur.com/Z6XbK6R.png"

DATA_FILE = "data.json"

# ===== DATA =====
def load_data():
    try:
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    except:
        return {"users": {}, "history": [], "total": 0}

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)

data = load_data()

# ===== USER =====
def save_user(user_id):
    data["users"][str(user_id)] = {
        "last_active": str(datetime.now()),
        "banned": data["users"].get(str(user_id), {}).get("banned", False)
    }
    save_data(data)

def is_banned(user_id):
    return data["users"].get(str(user_id), {}).get("banned", False)

# ===== JOIN CHECK =====
async def check_join(user_id, bot):
    try:
        member = await bot.get_chat_member(CHANNEL, user_id)
        return member.status in ["member", "administrator", "creator"]
    except:
        return False

# ===== FORMAT =====
def format_number(num):
    num = num.strip().replace(" ", "").replace("-", "")
    if num.startswith("+"):
        num = num[1:]
    if len(num) < 8 or len(num) > 15:
        return None
    return num

# ===== GENERATE =====
def generate_links(numbers):
    result = []
    count = 0
    for i, num in enumerate(numbers, start=1):
        f = format_number(num)
        if f:
            result.append(f"{i}. https://wa.me/{f}")
            count += 1
    return result, count

# ===== LOG =====
def log_history(user_id, count):
    data["history"].append({
        "user_id": user_id,
        "count": count,
        "time": str(datetime.now())
    })
    data["total"] += count
    save_data(data)

# ===== MENU =====
def main_menu(is_admin=False):
    menu = [
        [" Number Check"],
        [" My History"],
        [" Support"]
    ]
    if is_admin:
        menu.append([" Broadcast"])
        menu.append([" Admin Panel"])
    return ReplyKeyboardMarkup(menu, resize_keyboard=True)

# ===== START =====
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if not await check_join(user_id, context.bot):
        keyboard = [[InlineKeyboardButton(" Join Channel", url=f"https://t.me/{CHANNEL[1:]}")]]
        await update.message.reply_text("  channel join ", reply_markup=InlineKeyboardMarkup(keyboard))
        return

    save_user(user_id)

    # LOGO AUTO SEND
    await update.message.reply_photo(
        photo=LOGO_URL,
        caption=" *ST WHATAPPS CHEKAR BOT*\n\n Fast & Clean Checker\n Track History",
        parse_mode="Markdown",
        reply_markup=main_menu(user_id == ADMIN_ID)
    )

# ===== TEXT =====
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text

    if not await check_join(user_id, context.bot):
        await update.message.reply_text("  channel join ")
        return

    if is_banned(user_id):
        await update.message.reply_text("  banned")
        return

    save_user(user_id)

    if text == " Number Check":
        await update.message.reply_text("   (line by line)")
        return

    if text == " My History":
        records = [r for r in data["history"] if r["user_id"] == user_id]
        total = sum(r["count"] for r in records)

        msg = f" *Your History*\n\nTotal: {total}\n\n"
        for r in records[-5:]:
            msg += f"{r['count']}  {r['time'][:16]}\n"

        await update.message.reply_text(msg, parse_mode="Markdown")
        return

    if text == " Support":
        await update.message.reply_text(f" {SUPPORT}")
        return

    # ===== BROADCAST =====
    if text == " Broadcast" and user_id == ADMIN_ID:
        context.user_data["broadcast"] = True
        await update.message.reply_text(" message ")
        return

    if context.user_data.get("broadcast"):
        context.user_data["broadcast"] = False
        for uid in data["users"]:
            try:
                await context.bot.send_message(int(uid), text)
            except:
                pass
        await update.message.reply_text(" Broadcast Done")
        return

    # ===== PROCESS =====
    numbers = text.split("\n")
    links, count = generate_links(numbers)
    log_history(user_id, count)

    result = "\n".join(links)
    context.user_data["result"] = result

    keyboard = [[InlineKeyboardButton(" Copy All Results", callback_data="copy")]]

    await update.message.reply_text(
        f" *Checked {count} Numbers*\n\n{result[:3500]}",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

# ===== COPY =====
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    result = context.user_data.get("result", "")

    if result:
        for i in range(0, len(result), 4000):
            await query.message.reply_text(result[i:i+4000])

# ===== RUN =====
keep_alive()

app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT, handle_text))
app.add_handler(CallbackQueryHandler(button))

app.run_polling()
