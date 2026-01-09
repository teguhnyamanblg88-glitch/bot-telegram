from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
import os

TOKEN = os.getenv("TOKEN")  # nanti di Railway / Heroku
OWNER_ID = int(os.getenv("OWNER_ID"))  # ID telegram kamu

# /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ Bot hidup & siap menerima video")

# terima video
async def handle_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        await update.message.reply_text("⛔ Bot private")
        return

    # VIDEO
    if update.message.video:
        file_id = update.message.video.file_id

    # DOCUMENT VIDEO
    elif update.message.document and update.message.document.mime_type.startswith("video"):
        file_id = update.message.document.file_id

    else:
        await update.message.reply_text("Bukan video")
        return

    # kirim ulang video
    await update.message.reply_video(file_id)

app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.VIDEO | filters.Document.VIDEO, handle_video))

print("Bot berjalan...")
app.run_polling()
