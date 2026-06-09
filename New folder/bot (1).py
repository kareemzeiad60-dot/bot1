import os
import re
import json
import hashlib
import logging
import time
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from telegram import Update
from telegram.ext import (
    Application,
    MessageHandler,
    TypeHandler,
    filters,
    ContextTypes,
)
from telegram.error import Conflict, NetworkError
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.environ.get("BOT_TOKEN", "").strip()
CHANNEL_ID = os.environ.get("CHANNEL_ID", "").strip()
KEYWORDS = [k.strip() for k in os.environ.get("KEYWORD", "").split(",") if k.strip()]
GROUP_IDS = [g.strip() for g in os.environ.get("GROUP_ID", "").split(",") if g.strip()]
BLOCKED_WORDS = [w.strip() for w in os.environ.get("BLOCKED_WORDS", "").split(",") if w.strip()]

SENT_HASHES_FILE = "sent_hashes.json"
sent_hashes: set = set()
sent_hashes_lock = threading.Lock()


def load_sent_hashes():
    global sent_hashes
    if os.path.exists(SENT_HASHES_FILE):
        try:
            with open(SENT_HASHES_FILE, "r") as f:
                sent_hashes = set(json.load(f))
            logger.info(f"Loaded {len(sent_hashes)} sent message hashes.")
        except Exception as e:
            logger.warning(f"Could not load sent hashes: {e}")
            sent_hashes = set()


def save_sent_hash(h: str):
    with sent_hashes_lock:
        sent_hashes.add(h)
        try:
            with open(SENT_HASHES_FILE, "w") as f:
                json.dump(list(sent_hashes), f)
        except Exception as e:
            logger.warning(f"Could not save sent hash: {e}")


def make_hash(text: str) -> str:
    return hashlib.md5(text.strip().encode("utf-8")).hexdigest()


def has_numbers(text: str) -> bool:
    return bool(re.search(r'[0-9٠-٩]', text))


class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"OK")

    def log_message(self, format, *args):
        pass


def run_health_server():
    server = HTTPServer(("0.0.0.0", 8080), HealthHandler)
    server.serve_forever()


async def debug_all_updates(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"[DEBUG] Update received: {update.to_dict()}")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message or update.channel_post
    if not message:
        return

    if not KEYWORDS:
        return

    text = message.text or message.caption or ""
    chat_id = message.chat.id
    chat_type = message.chat.type
    logger.info(f"[MSG] chat_id={chat_id} type={chat_type} text='{text[:60]}'")

    if GROUP_IDS and str(chat_id) not in GROUP_IDS:
        logger.info(f"[SKIP] Message from unknown group {chat_id}, allowed: {GROUP_IDS}")
        return

    matched = any(kw in text for kw in KEYWORDS)
    if not matched:
        logger.info(f"[SKIP] No keyword matched in message.")
        return

    if BLOCKED_WORDS and any(bw in text for bw in BLOCKED_WORDS):
        logger.info(f"[SKIP] Message contains a blocked word.")
        return


    if not has_numbers(text):
        logger.info(f"[SKIP] Message has no numbers, skipping.")
        return

    msg_hash = make_hash(text)
    with sent_hashes_lock:
        if msg_hash in sent_hashes:
            logger.info(f"[SKIP] Duplicate message, already forwarded.")
            return

    logger.info(f"[MATCH] Keyword found! Forwarding to channel...")

    try:
        forwarded = False

        if message.photo:
            photo = message.photo[-1]
            await context.bot.send_photo(
                chat_id=CHANNEL_ID,
                photo=photo.file_id,
                caption=text if text else None,
            )
            forwarded = True
            logger.info("Photo forwarded to channel.")

        elif message.video:
            await context.bot.send_video(
                chat_id=CHANNEL_ID,
                video=message.video.file_id,
                caption=text if text else None,
            )
            forwarded = True
            logger.info("Video forwarded to channel.")

        elif message.animation:
            await context.bot.send_animation(
                chat_id=CHANNEL_ID,
                animation=message.animation.file_id,
                caption=text if text else None,
            )
            forwarded = True
            logger.info("GIF forwarded to channel.")

        elif message.document:
            await context.bot.send_document(
                chat_id=CHANNEL_ID,
                document=message.document.file_id,
                caption=text if text else None,
            )
            forwarded = True
            logger.info("Document forwarded to channel.")

        elif message.audio:
            await context.bot.send_audio(
                chat_id=CHANNEL_ID,
                audio=message.audio.file_id,
                caption=text if text else None,
            )
            forwarded = True
            logger.info("Audio forwarded to channel.")

        elif message.voice:
            await context.bot.send_voice(
                chat_id=CHANNEL_ID,
                voice=message.voice.file_id,
            )
            forwarded = True
            logger.info("Voice forwarded to channel.")

        elif message.sticker:
            await context.bot.send_sticker(
                chat_id=CHANNEL_ID,
                sticker=message.sticker.file_id,
            )
            forwarded = True
            logger.info("Sticker forwarded to channel.")

        else:
            if text:
                await context.bot.send_message(
                    chat_id=CHANNEL_ID,
                    text=text,
                )
                forwarded = True
                logger.info("Text message forwarded to channel.")

        if forwarded:
            save_sent_hash(msg_hash)

    except Exception as e:
        logger.error(f"Error sending to channel: {e}")


def build_app():
    msg_filter = (
        filters.TEXT
        | filters.PHOTO
        | filters.VIDEO
        | filters.ANIMATION
        | filters.Document.ALL
        | filters.AUDIO
        | filters.VOICE
        | filters.Sticker.ALL
    )
    a = Application.builder().token(BOT_TOKEN).build()
    a.add_handler(TypeHandler(Update, debug_all_updates), group=-1)
    a.add_handler(MessageHandler(msg_filter & ~filters.COMMAND, handle_message))
    return a


def main():
    if not BOT_TOKEN:
        logger.error("BOT_TOKEN is not set.")
        return
    if not CHANNEL_ID:
        logger.error("CHANNEL_ID is not set.")
        return
    if not KEYWORDS:
        logger.error("KEYWORD is not set.")
        return

    logger.info(f"Bot starting... Keywords: {KEYWORDS} | Channel: {CHANNEL_ID} | Groups: {GROUP_IDS if GROUP_IDS else 'ALL'}")

    load_sent_hashes()

    health_thread = threading.Thread(target=run_health_server, daemon=True)
    health_thread.start()
    logger.info("Health check server started on port 8080")

    app = build_app()

    while True:
        try:
            logger.info("Bot is running and listening for messages...")
            app.run_polling(
                allowed_updates=Update.ALL_TYPES,
                drop_pending_updates=True,
            )
            logger.warning("run_polling exited. Restarting in 15 seconds...")
            time.sleep(15)
            app = build_app()
        except Conflict:
            logger.warning("Conflict: another instance detected. Waiting 15 seconds before retry...")
            time.sleep(15)
            app = build_app()
        except NetworkError as e:
            logger.warning(f"Network error: {e}. Retrying in 10 seconds...")
            time.sleep(10)
            app = build_app()
        except KeyboardInterrupt:
            logger.info("Bot stopped by user.")
            break
        except Exception as e:
            logger.error(f"Unexpected error: {e}. Retrying in 10 seconds...")
            time.sleep(10)
            app = build_app()


if __name__ == "__main__":
    main()
