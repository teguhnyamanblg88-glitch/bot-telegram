from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters
)
from telegram import Update
import os

# TOKEN dari Render Environment Variable
TOKEN = os.getenv("BOT_TOKEN")

# ===== FUNGSI DEBUG FILE_ID =====
async def get_file_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.video:
        await update.message.reply_text(update.message.video.file_id)

# ===== BUILD APP =====
app = ApplicationBuilder().token(TOKEN).build()

# ===== DAFTARKAN HANDLER =====
app.add_handler(MessageHandler(filters.VIDEO, get_file_id))

# ===== JALANKAN BOT =====
app.run_polling()
