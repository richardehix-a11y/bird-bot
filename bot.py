import os, glob
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import yt_dlp

TOKEN = os.getenv("BOT_TOKEN")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔥 Bird Bot LIVE 24/7\nSend TikTok / Insta link")

async def download(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text
    if "http" not in url: return
    m = await update.message.reply_text("⚡ Downloading...")
    try:
        for f in glob.glob("video.*"):
            try: os.remove(f)
            except: pass
        with yt_dlp.YoutubeDL({'outtmpl':'video.%(ext)s','format':'best','quiet':True}) as ydl:
            ydl.download([url])
        f = glob.glob("video.*")[0]
        await update.message.reply_video(open(f,'rb'))
        os.remove(f)
        await m.delete()
    except Exception as e:
        await m.edit_text(f"Error: {e}")

app = Application.builder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, download))
app.run_polling()
