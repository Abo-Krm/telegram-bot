import os
import re
import yt_dlp
import instaloader
import threading

from flask import Flask
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, ContextTypes, filters

# =======================
# ENV TOKEN
# =======================
TOKEN = os.getenv("BOT_TOKEN")

# =======================
# FLASK WEB SERVER (REQUIRED FOR RENDER)
# =======================
app_web = Flask(__name__)

@app_web.route("/")
def home():
    return "Bot is running"

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app_web.run(host="0.0.0.0", port=port)

# =======================
# INSTALOADER SETUP
# =======================
L = instaloader.Instaloader(
    download_videos=True,
    download_video_thumbnails=False,
    download_comments=False,
    save_metadata=False,
    post_metadata_txt_pattern=""
)

# =======================
# MESSAGE HANDLER
# =======================
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):

    text = update.message.text.strip()

    await update.message.reply_text("⏳ Processing your link...")

    if not os.path.exists("downloads"):
        os.mkdir("downloads")

    try:

        # =======================
        # TIKTOK (yt-dlp)
        # =======================
        if "tiktok.com" in text:

            ydl_opts = {
                "outtmpl": "downloads/%(title)s.%(ext)s",
                "format": "best"
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(text, download=True)
                filename = ydl.prepare_filename(info)

            with open(filename, "rb") as video:
                await update.message.reply_video(video=video)

            os.remove(filename)

        # =======================
        # INSTAGRAM
        # =======================
        elif "instagram.com" in text:

            shortcode = re.search(r"/(p|reel|tv)/([^/?]+)/", text)

            if not shortcode:
                await update.message.reply_text("❌ Invalid Instagram link")
                return

            code = shortcode.group(2)

            post = instaloader.Post.from_shortcode(L.context, code)

            L.download_post(post, target="downloads")

            files = os.listdir("downloads")

            for file in files:

                path = f"downloads/{file}"

                if file.endswith(".mp4"):
                    with open(path, "rb") as video:
                        await update.message.reply_video(video=video)

                elif file.endswith(".jpg"):
                    with open(path, "rb") as photo:
                        await update.message.reply_photo(photo=photo)

                os.remove(path)

        else:
            await update.message.reply_text("❌ Send Instagram or TikTok link only")

    except Exception as e:
        await update.message.reply_text("⚠️ Error downloading media")
        print(e)

# =======================
# START BOT
# =======================
def main():

    # start flask web server (IMPORTANT FOR RENDER)
    threading.Thread(target=run_web).start()

    # telegram bot
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Bot running...")

    app.run_polling()

# =======================
# ENTRY POINT
# =======================
if __name__ == "__main__":
    main()
