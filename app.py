import os
import asyncio
from flask import Flask, request
from telegram import Update
from production_bot import AdvancedBot

app = Flask(__name__)
bot = AdvancedBot()
PORT = int(os.environ.get("PORT", 5000))
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# ✅ تأكد من تهيئة التطبيق (Application)
asyncio.run(bot.application.initialize())

# Health check
@app.route("/health")
def health():
    return {"status": "healthy"}

# Webhook endpoint
@app.route(f"/webhook/{TOKEN}", methods=["POST"])
def webhook():
    try:
        update = Update.de_json(request.get_json(), bot.application.bot)
        asyncio.run(bot.application.process_update(update))
    except Exception as e:
        app.logger.error(f"Webhook error: {e}")
        return {"ok": False, "error": str(e)}, 500
    return {"ok": True}

@app.route("/")
def index():
    return "🤖 البوت يعمل بشكل كامل الآن!"

if __name__ == "__main__":
    bot.run_webhook(port=PORT, url_path=TOKEN, webhook_url=WEBHOOK_URL)
