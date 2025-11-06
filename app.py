# app.py  -- for Render (webhook using Flask + clean asyncio lifecycle)
import os
import logging
import signal
import asyncio
from flask import Flask, request, jsonify
from telegram import Update
from production_bot import AdvancedBot   # تأكدي من اسم الفئة والمسار

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# إنشاء بوت - لا تطلبي run_polling/run_webhook هنا
bot = AdvancedBot()

PORT = int(os.environ.get("PORT", 5000))
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")  # يجب أن يكون مُعيّنًا
WEBHOOK_URL = os.getenv("WEBHOOK_URL")   # مثال: https://your-app.onrender.com/webhook

if not TOKEN:
    raise RuntimeError("TELEGRAM_BOT_TOKEN must be set in environment variables")

# ===== create & set a dedicated event loop for the Flask process =====
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)

# ===== initialize Application (but do NOT call start()) =====
# initialize gives you a ready-to-use `bot.application.bot` and handlers,
# but avoids launching background fetchers/tasks that start with start()
async def _init_app():
    await bot.application.initialize()   # prepares internal resources
    # do NOT call `await bot.application.start()` — avoids background fetcher
    logger.info("✅ Bot.application initialized (no background fetcher started)")

loop.run_until_complete(_init_app())

# ===== graceful shutdown coroutine =====
async def _shutdown_coro():
    logger.info("🛑 shutdown coroutine started: stopping and shutting down Application...")
    try:
        # If you ever started job queue or other components, stop them first:
        # await bot.application.stop()   # not called earlier, but keep for safety
        await bot.application.shutdown()   # release handlers, cancel tasks cleanly
        logger.info("✅ application.shutdown() completed")
    except Exception as e:
        logger.exception("❌ Exception during application.shutdown(): %s", e)
    finally:
        logger.info("Stopping event loop")
        # stop the loop from within itself
        loop.call_soon_threadsafe(loop.stop)

# signal handler that schedules the coroutine on our loop
def _on_signal(sig, frame):
    logger.info("Signal %s received — scheduling shutdown", sig)
    # use run_coroutine_threadsafe to schedule on the loop from signal handler
    asyncio.run_coroutine_threadsafe(_shutdown_coro(), loop)

# register handlers for Render (SIGTERM) and local Ctrl-C (SIGINT)
signal.signal(signal.SIGTERM, _on_signal)
signal.signal(signal.SIGINT, _on_signal)

# ===== webhook endpoint: accept update and schedule processing =====
@app.route(f"/webhook/{TOKEN}", methods=["POST"])
def webhook():
    try:
        data = request.get_json(force=True)
        update = Update.de_json(data, bot.application.bot)
        # Schedule processing on our loop; return HTTP 200 immediately.
        loop.create_task(bot.application.process_update(update))
        return jsonify({"ok": True})
    except Exception as e:
        logger.exception("Webhook handling failed: %s", e)
        return jsonify({"ok": False, "error": str(e)}), 500

@app.route("/health")
def health():
    return jsonify({"status": "healthy"})

@app.route("/")
def index():
    return "🤖 Bot running with robust webhook lifecycle"

# ===== main: we don't call bot.application.run_webhook() here =====
# Render runs gunicorn which imports this module and serves `app`.
# Only for local debug:
if __name__ == "__main__":
    logger.info("Starting Flask dev server (for debug only)")
    app.run(host="0.0.0.0", port=PORT)
