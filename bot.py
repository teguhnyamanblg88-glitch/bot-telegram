import os
import time
import json
import aiohttp
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# ================== CONFIG ==================
TOKEN = os.getenv("TOKEN")
OWNER_ID = int(os.getenv("OWNER_ID", "0"))
SHEET_API = os.getenv("SHEET_API")
CHANNEL_ID = os.getenv("CHANNEL_ID")  # WAJIB numeric ID -100xxxx
CHANNEL_LINK = "https://t.me/+Au-WBvKA2HU2ZTA9"

ALLOWED_GROUPS = [
    # -1001234567890
]

# ================== RATE LIMIT ==================
user_upload_history = {}

def is_rate_limited(user_id, limit=5, interval=60):
    now = time.time()
    history = user_upload_history.get(user_id, [])
    history = [t for t in history if now - t < interval]
    if len(history) >= limit:
        return True
    history.append(now)
    user_upload_history[user_id] = history
    return False

# ================== SUBSCRIBE CHECK ==================
async def check_subscribe(user_id, context):
    if not CHANNEL_ID:
        return True
    try:
        member = await context.bot.get_chat_member(
            chat_id=int(CHANNEL_ID),
            user_id=user_id
        )
        return member.status in ("member", "administrator", "creator")
    except:
        return False

# ================== SHEET SERVICE ==================
async def save_to_sheet(video_key, file_id, judul=""):
    if not SHEET_API:
        return None

    payload = {
        "video_id": video_key,
        "file_id": file_id,
        "judul": judul
    }

    timeout = aiohttp.ClientTimeout(total=15)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        try:
            async with session.post(SHEET_API, json=payload) as resp:
                return resp.status
        except Exception as e:
            print(f"SHEET SAVE ERROR: {e}")
            return None

async def get_from_sheet(video_key):
    if not SHEET_API:
        return None

    timeout = aiohttp.ClientTimeout(total=15)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        try:
            async with session.get(SHEET_API, params={"video_id": video_key}) as resp:
                text = await resp.text()
                return None if text == "NOT_FOUND" else text
        except Exception as e:
            print(f"SHEET GET ERROR: {e}")
            return None

# ================== START ==================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if OWNER_ID and user_id != OWNER_ID:
        if not await check_subscribe(user_id, context):
            keyboard = [[InlineKeyboardButton("📢 Bergabung ke Channel", url=CHANNEL_LINK)]]
            await update.message.reply_text(
                "⚠️ **AKSES DIBATASI**\n\n"
                "Silakan join channel terlebih dahulu lalu klik /start ulang.",
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="Markdown"
            )
            return

    if context.args:
        video_id = context.args[0]

        # Langsung kirim jika File ID
        if len(video_id) > 50:
            try:
                await update.message.reply_video(video_id)
                return
            except:
                pass

        file_id = await get_from_sheet(video_id)
        if not file_id:
            await update.message.reply_text("❌ Video tidak ditemukan")
            return

        await update.message.reply_video(file_id)
    else:
        await update.message.reply_text("✅ Bot siap. Kirim video untuk disimpan.")

# ================== SAVE VIDEO PRIVATE ==================
async def save_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    if OWNER_ID and user.id != OWNER_ID:
        await update.message.reply_text("⛔ Bot private")
        return

    if is_rate_limited(user.id):
        await update.message.reply_text("⏳ Terlalu cepat, coba lagi sebentar")
        return

    file_id = None
    if update.message.video:
        file_id = update.message.video.file_id
    elif update.message.document and update.message.document.mime_type.startswith("video"):
        file_id = update.message.document.file_id

    if not file_id:
        await update.message.reply_text("❌ Bukan video")
        return

    caption = update.message.caption or ""
    judul = ""

    if "|" in caption:
        video_key, judul = map(str.strip, caption.split("|", 1))
    elif caption.strip():
        video_key = caption.strip()
    else:
        video_key = f"VID_{update.effective_chat.id}_{update.message.message_id}"

    await save_to_sheet(video_key, file_id, judul)

    bot_username = (await context.bot.get_me()).username
    link = f"https://t.me/{bot_username}?start={video_key}"

    await update.message.reply_text(
        f"✅ Video disimpan\n"
        f"ID: {video_key}\n"
        f"{f'Judul: {judul}\n' if judul else ''}"
        f"\n🔗 {link}"
    )

# ================== GROUP HANDLER ==================
async def debug_group(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id

    if ALLOWED_GROUPS and chat_id not in ALLOWED_GROUPS:
        return

    file_id = None
    if update.message.video:
        file_id = update.message.video.file_id
    elif update.message.document and update.message.document.mime_type.startswith("video"):
        file_id = update.message.document.file_id

    if not file_id:
        return

    try:
        video_key = f"GRP_{chat_id}_{update.message.message_id}"
        judul = (update.message.caption or "Video dari Group")[:50]

        await save_to_sheet(video_key, file_id, judul)

        bot_username = (await context.bot.get_me()).username
        link = f"https://t.me/{bot_username}?start={video_key}"

        await context.bot.send_message(
            chat_id=OWNER_ID,
            text=f"🎥 Video Group Disimpan\nID: {video_key}\n🔗 {link}"
        )
    except Exception as e:
        print(f"GROUP ERROR: {e}")

# ================== MAIN ==================
def main():
    if not TOKEN:
        print("TOKEN belum diset")
        return

    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(
        MessageHandler(
            filters.ChatType.PRIVATE & (filters.VIDEO | filters.Document.VIDEO),
            save_video
        )
    )
    app.add_handler(
        MessageHandler(filters.ChatType.GROUPS, debug_group)
    )

    print("🤖 Bot Production Running...")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
