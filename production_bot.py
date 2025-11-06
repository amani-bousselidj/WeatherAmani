import os
import logging
import sqlite3
import requests
from datetime import datetime
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)

class AdvancedBot:
    def __init__(self):
        self.token = os.getenv("TELEGRAM_BOT_TOKEN")
        if not self.token:
            raise ValueError("❌ TELEGRAM_BOT_TOKEN مطلوب!")

        # إعداد التطبيق الحديث
        self.application = Application.builder().token(self.token).build()

        # إعداد قاعدة البيانات
        self.conn = sqlite3.connect('bot.db', check_same_thread=False)
        self.cursor = self.conn.cursor()
        self.إعداد_قاعدة_بيانات()

        # إعداد handlers
        self.application.add_handler(CommandHandler("start", self.start))
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.echo))

    def إعداد_قاعدة_بيانات(self):
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            join_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )''')
        self.conn.commit()

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        self.cursor.execute('INSERT OR IGNORE INTO users(user_id, username, first_name) VALUES (?, ?, ?)',
                            (user.id, user.username, user.first_name))
        self.conn.commit()
        await update.message.reply_text(f"🚀 مرحبا {user.first_name}!")

    async def echo(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text(f"لقد قلت: {update.message.text}")

    def run_webhook(self, port: int, url_path: str, webhook_url: str):
        self.application.run_webhook(
            listen="0.0.0.0",
            port=port,
            url_path=url_path,
            webhook_url=f"{webhook_url}/{url_path}"
        )
