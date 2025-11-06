import os
import asyncio
import logging
import signal
from flask import Flask, request
from telegram import Update
from production_bot import AdvancedBot

# إعداد السجل
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
bot = AdvancedBot()

PORT = int(os.environ.get("PORT", 5000))
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)

async def init_bot():
    await bot.application.initialize()
    await bot.application.start()
    logger.info("✅ Telegram Bot initialized and started successfully")

# ✅ تشغيل التهيئة مرة واحدة
loop.run_until_complete(init_bot())

# ✅ إيقاف نظيف عند shutdown
def shutdown_handler(*_):
    logger.info("🛑 Shutting down bot gracefully...")
    try:
        loop.run_until_complete(bot.application.stop())
        loop.run_until_complete(bot.application.shutdown())
    except Exception as e:
        logger.error(f"Error while shutting down: {e}")
    finally:
        loop.stop()
        logger.info("✅ Bot stopped cleanly")

# تسجيل إشارات النظام (SIGTERM من Render)
signal.signal(signal.SIGTERM, shutdown_handler)
signal.signal(signal.SIGINT, shutdown_handler)

@app.route("/health")
def health():
    return {"status": "healthy"}

@app.route(f"/webhook/{TOKEN}", methods=["POST"])
def webhook():
    try:
        data = request.get_json(force=True)
        update = Update.de_json(data, bot.application.bot)
        loop.create_task(bot.application.process_update(update))
        return {"ok": True}
    except Exception as e:
        logger.error(f"❌ Webhook error: {e}")
        return {"ok": False, "error": str(e)}, 500

@app.route("/")
def index():
    return "🤖 البوت الآن يعمل بثبات على Render!"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT)
