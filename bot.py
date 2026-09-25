import os
import asyncio
import tempfile
import yt_dlp
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

BOT_TOKEN = os.getenv("BOT_TOKEN")

# --- Download function (runs in background) ---
def download_video(url):
    temp_dir = tempfile.mkdtemp()
    output_template = os.path.join(temp_dir, '%(title).50s.%(ext)s')

    ydl_opts = {
        'format': 'bestvideo[ext=mp4][height<=1080]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        'outtmpl': output_template,
        'noplaylist': True,
        'quiet': True,
        'merge_output_format': 'mp4',
        'max_filesize': 1900 * 1024 * 1024, # Telegram max 2GB
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            # Fix filename if merged to mp4
            if not os.path.exists(filename):
                filename = os.path.splitext(filename)[0] + ".mp4"
            return filename, info.get('title', 'Video')
    except Exception as e:
        return None, str(e)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Welcome to Naija Downloader!\n\n"
        "Just send me any link from:\n"
        "TikTok, Instagram, Facebook, Twitter/X, YouTube, Pinterest\n\n"
        "I will download it without watermark."
    )

async def handle_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()

    if not url.startswith("http"):
        await update.message.reply_text("Please send a valid video link.")
        return

    msg = await update.message.reply_text("⏳ Downloading... please wait")

    loop = asyncio.get_event_loop()
    filepath, title = await loop.run_in_executor(None, download_video, url)

    if not filepath or not os.path.exists(filepath):
        await msg.edit_text(f"❌ Failed: {title}\n\nTry another link. Some private IG/TikTok videos need login.")
        return

    file_size = os.path.getsize(filepath) / (1024 * 1024) # in MB
    await msg.edit_text(f"✅ Downloaded ({file_size:.1f} MB) - Now uploading to Telegram...")

    try:
        # Telegram now allows up to 2000MB
        await update.message.reply_video(
            video=open(filepath, 'rb'),
            caption=f"✅ {title}",
            supports_streaming=True
        )
        await msg.delete()
    except Exception as e:
        # If too large for video, try as document
        try:
            await update.message.reply_document(
                document=open(filepath, 'rb'),
                caption=f"✅ {title} (sent as file due to size)"
            )
            await msg.delete()
        except Exception as e2:
            await msg.edit_text(f"❌ File too large for Telegram: {file_size:.1f}MB\nError: {e2}")
    finally:
        # Cleanup
        try:
            os.remove(filepath)
            os.rmdir(os.path.dirname(filepath))
        except:
            pass

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_link))
    print("Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
