import os
from flask import Flask, request
from telegram import Update
from production_bot import AdvancedBot


app = Flask(__name__)
bot = AdvancedBot()
PORT = int(os.environ.get("PORT", 5000))
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# Health check
@app.route("/health")
def health():
    return {"status": "healthy"}

# Webhook endpoint
@app.route(f"/webhook/{TOKEN}", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(), bot.application.bot)
    bot.application.process_update(update)
    return {"ok": True}

@app.route("/")
def index():
    return "🤖 البوت يعمل!"

if __name__ == "__main__":
    bot.run_webhook(port=PORT, url_path=TOKEN, webhook_url=WEBHOOK_URL)
