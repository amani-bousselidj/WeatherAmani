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

# إعداد البوت
bot = AdvancedBot()

# البيئة
PORT = int(os.environ.get("PORT", 5000))
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# ✅ إنشاء حلقة asyncio واحدة
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)

async def init_bot():
    await bot.application.initialize()
    await bot.application.start()
    logger.info("✅ Telegram Bot initialized and started successfully")

# تشغيل التهيئة لمرة واحدة عند بدء السيرفر
loop.run_until_complete(init_bot())

# Health check
@app.route("/health")
def health():
    return {"status": "healthy"}

# ✅ Webhook endpoint
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

# ✅ لا نشغّل run_webhook() إطلاقًا
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT)
    logger.info(f"🚀 Flask server running on port {PORT}")