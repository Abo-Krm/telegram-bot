import os
import re
import yt_dlp
import instaloader

from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, ContextTypes, filters

TOKEN = os.getenv("BOT_TOKEN")
# Initialize Instagram loader
L = instaloader.Instaloader(
    download_videos=True,
    download_video_thumbnails=False,
    download_comments=False,
    save_metadata=False,
    post_metadata_txt_pattern=""
)


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):

    text = update.message.text.strip()

    await update.message.reply_text("⏳ Processing your link...")

    # Create temp folder
    if not os.path.exists("downloads"):
        os.mkdir("downloads")

    try:

        # TikTok / Video (yt-dlp)
        if "tiktok.com" in text:

            ydl_opts = {
                "outtmpl": "downloads/%(title)s.%(ext)s",
                "format": "best"
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(text, download=True)
                filename = ydl.prepare_filename(info)

            await update.message.reply_video(video=open(filename, "rb"))

            os.remove(filename)


        # Instagram
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
                    await update.message.reply_video(video=open(path, "rb"))

                elif file.endswith(".jpg"):
                    await update.message.reply_photo(photo=open(path, "rb"))

                os.remove(path)


        else:
            await update.message.reply_text("❌ Send Instagram or TikTok link only")


    except Exception as e:

        await update.message.reply_text("⚠️ Error downloading media")
        print(e)


def main():

    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Bot running...")

    app.run_polling()


if __name__ == "__main__":
    main()
