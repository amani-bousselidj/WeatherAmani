import os
import asyncio
import logging
from flask import Flask, request
from telegram import Update
from production_bot import AdvancedBot

# إعداد السجل
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# إعداد Flask
app = Flask(__name__)
bot = AdvancedBot()

PORT = int(os.environ.get("PORT", 5000))
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# ✅ نُهيئ التطبيق مرة واحدة فقط
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)

async def init_bot():
    await bot.application.initialize()
    await bot.application.start()
    logger.info("✅ Telegram Bot initialized and started successfully")

loop.run_until_complete(init_bot())

# Health Check
@app.route("/health")
def health():
    return {"status": "healthy"}

# ✅ Webhook endpoint
@app.route(f"/webhook/{TOKEN}", methods=["POST"])
def webhook():
    try:
        data = request.get_json(force=True)
        update = Update.de_json(data, bot.application.bot)
        # نستخدم create_task داخل event loop الرئيسي
        loop.create_task(bot.application.process_update(update))
        return {"ok": True}
    except Exception as e:
        logger.error(f"❌ Webhook error: {e}")
        return {"ok": False, "error": str(e)}, 500

@app.route("/")
def index():
    return "🤖 البوت الآن يعمل بثبات على Render!"

if __name__ == "__main__":
    bot.application.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        url_path=TOKEN,
        webhook_url=f"{WEBHOOK_URL}/{TOKEN}"
    )
    logger.info(f"🚀 Bot is running on port {PORT} with webhook URL {WEBHOOK_URL}/{TOKEN}")