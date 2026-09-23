import os
import threading
from flask import Flask
import yt_dlp
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes, CommandHandler

# --- FAKE WEB SERVER TO FIX RENDER "No open ports" ERROR ---
app = Flask(__name__)
@app.route('/')
def home():
    return "Bot is running!"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

threading.Thread(target=run_flask, daemon=True).start()
# -------------------------------------------------------------

BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    print("ERROR: BOT_TOKEN not set in Environment!")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Send me any social media link (TikTok, Instagram, YouTube, Twitter, Facebook) and I will download the video for you! 📥"
    )

async def download_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()
    if not url.startswith("http"):
        return
    
    await update.message.reply_text("Downloading... ⏳ Please wait")

    try:
        ydl_opts = {
            'format': 'mp4/best',
            'outtmpl': 'video.%(ext)s',
            'noplaylist': True,
            'max_filesize': 100 * 1024 * 1024, # 100MB limit for Telegram
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)

        # Send video back
        with open(filename, 'rb') as f:
            await update.message.reply_video(video=f, caption="Here is your video ✅")

        # Clean up
        if os.path.exists(filename):
            os.remove(filename)

    except Exception as e:
        await update.message.reply_text(f"Failed to download ❌\nError: {str(e)[:200]}")
        print(e)

if __name__ == '__main__':
    telegram_app = ApplicationBuilder().token(BOT_TOKEN).build()
    telegram_app.add_handler(CommandHandler("start", start))
    telegram_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, download_video))
    print("Bot started...")
    telegram_app.run_polling()
