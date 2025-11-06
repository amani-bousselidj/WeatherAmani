import os
import asyncio
import logging
from flask import Flask, request
from telegram import Update
from production_bot import AdvancedBot

# إعداد Flask
app = Flask(__name__)
bot = AdvancedBot()

PORT = int(os.environ.get("PORT", 5000))
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

logging.basicConfig(level=logging.INFO)

# ✅ تأكدي من تهيئة التطبيق وتشغيله بشكل كامل قبل أي طلب
async def init_bot():
    await bot.application.initialize()
    await bot.application.start()
    logging.info("✅ Telegram Application initialized and started")

# نُشغل التهيئة داخل حدث غير متزامن مرة واحدة فقط
asyncio.get_event_loop().run_until_complete(init_bot())

# ✅ Health check
@app.route("/health")
def health():
    return {"status": "healthy"}

# ✅ Webhook endpoint
@app.route(f"/webhook/{TOKEN}", methods=["POST"])
def webhook():
    try:
        data = request.get_json(force=True)
        update = Update.de_json(data, bot.application.bot)
        bot.application.create_task(bot.application.process_update(update))
        return {"ok": True}
    except Exception as e:
        logging.error(f"❌ Webhook error: {e}")
        return {"ok": False, "error": str(e)}, 500

@app.route("/")
def index():
    return "🤖 البوت الآن يعمل بنجاح عبر Render!"

if __name__ == "__main__":
    bot.application.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        url_path=TOKEN,
        webhook_url=f"{WEBHOOK_URL}/{TOKEN}"
    )
