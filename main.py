import json
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, CallbackQueryHandler, filters, ContextTypes

# ===== CONFIG =====
TOKEN = "8502098422:AAHFtNfJEFAirvzvBrVOCoLqPKvmHHicDQ8"
ADMIN_ID = 6766447756
CHANNEL = "@ST_WHATAPPS_CHEKAR"
SUPPORT = "@SHANTO_VAI_OWNER_TX"

DATA_FILE = "data.json"

# ===== LOAD/SAVE =====
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

# ===== JOIN CHECK =====
async def check_join(user_id, bot):
    try:
        member = await bot.get_chat_member(CHANNEL, user_id)
        return member.status in ["member", "administrator", "creator"]
    except:
        return False

# ===== SAVE USER =====
def save_user(user_id):
    data["users"][str(user_id)] = {
        "last_active": str(datetime.now()),
        "banned": data["users"].get(str(user_id), {}).get("banned", False)
    }
    save_data(data)

# ===== BAN CHECK =====
def is_banned(user_id):
    return data["users"].get(str(user_id), {}).get("banned", False)

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
        ["🟢 📥 Number Check"],
        ["🔵 📊 My History"],
        ["🟣 🆘 Support"]
    ]
    if is_admin:
        menu.append(["🔴 📢 Broadcast"])
        menu.append(["👑 📊 Admin Panel"])
    return ReplyKeyboardMarkup(menu, resize_keyboard=True)

# ===== START =====
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if not await check_join(user_id, context.bot):
        keyboard = [[InlineKeyboardButton("🔔 Join Channel", url=f"https://t.me/{CHANNEL[1:]}")]]
        await update.message.reply_text("❗ আগে channel join করো", reply_markup=InlineKeyboardMarkup(keyboard))
        return

    save_user(user_id)

    await update.message.reply_text("🤖 Welcome!", reply_markup=main_menu(user_id == ADMIN_ID))

# ===== TEXT =====
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if not await check_join(user_id, context.bot):
        await update.message.reply_text("❗ আগে channel join করো")
        return

    if is_banned(user_id):
        await update.message.reply_text("🚫 তুমি banned")
        return

    save_user(user_id)

    text = update.message.text

    if text == "🟢 📥 Number Check":
        await update.message.reply_text("📩 নাম্বার পাঠাও")
        return

    if text == "🔵 📊 My History":
        records = [r for r in data["history"] if r["user_id"] == user_id]
        total = sum(r["count"] for r in records)

        msg = f"📊 Total Checked: {total}\n\n"
        for r in records[-5:]:
            msg += f"{r['count']} → {r['time'][:16]}\n"

        await update.message.reply_text(msg)
        return

    if text == "🟣 🆘 Support":
        await update.message.reply_text(f"📩 {SUPPORT}")
        return

    if text == "🔴 📢 Broadcast" and user_id == ADMIN_ID:
        context.user_data["broadcast"] = True
        await update.message.reply_text("📩 message পাঠাও")
        return

    if text == "👑 📊 Admin Panel" and user_id == ADMIN_ID:
        total_users = len(data["users"])

        active = 0
        for u in data["users"].values():
            last = datetime.fromisoformat(u["last_active"])
            if datetime.now() - last < timedelta(hours=24):
                active += 1

        msg = f"👥 Users: {total_users}\n🔥 Active: {active}\n📞 Checked: {data['total']}"
        await update.message.reply_text(msg)
        return

    # broadcast
    if context.user_data.get("broadcast"):
        context.user_data["broadcast"] = False

        for uid in data["users"]:
            try:
                await context.bot.send_message(int(uid), text)
            except:
                pass

        await update.message.reply_text("✅ Done")
        return

    # numbers
    numbers = text.split("\n")
    links, count = generate_links(numbers)

    log_history(user_id, count)

    result = "\n".join(links)

    keyboard = [[InlineKeyboardButton("📋 Copy All", callback_data="copy")]]
    context.user_data["result"] = result

    await update.message.reply_text(result[:4000], reply_markup=InlineKeyboardMarkup(keyboard))

# ===== COPY =====
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.message.reply_text(context.user_data.get("result", ""))

# ===== BAN =====
async def ban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    uid = context.args[0]
    data["users"].setdefault(uid, {})["banned"] = True
    save_data(data)
    await update.message.reply_text("🚫 Banned")

async def unban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    uid = context.args[0]
    data["users"].setdefault(uid, {})["banned"] = False
    save_data(data)
    await update.message.reply_text("✅ Unbanned")

# ===== RUN =====
app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT, handle_text))
app.add_handler(CallbackQueryHandler(button))
app.add_handler(CommandHandler("ban", ban))
app.add_handler(CommandHandler("unban", unban))

app.run_polling()
