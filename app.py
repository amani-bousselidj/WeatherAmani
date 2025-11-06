# app.py
from flask import Flask, request, jsonify
import os
from production_bot import TelegramAdvancedBot
from telegram import Update

app = Flask(__name__)
bot = TelegramAdvancedBot()

@app.route("/")
def home():
    return "🤖 البوت يعمل!"

@app.route("/webhook/<token>", methods=["POST"])
def webhook(token):
    if token == bot.token:
        update = Update.de_json(request.get_json(), bot.application.bot)
        bot.application.process_update(update)
        return jsonify({"status": "ok"})
    return jsonify({"status": "error"}), 403

@app.route("/health")
def health():
    return jsonify({"status": "healthy"})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
