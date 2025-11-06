# bot.py
import os
import logging
import sqlite3
from datetime import datetime
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AdvancedBot:
    def __init__(self, token: str):
        if not token:
            raise ValueError("TELEGRAM_BOT_TOKEN مفقود ❌")
        self.token = token
        self.application = Application.builder().token(self.token).build()

        # إعداد قاعدة البيانات
        self.conn = sqlite3.connect('bot.db', check_same_thread=False)
        self.cursor = self.conn.cursor()
        self._setup_db()

        # تسجيل الأوامر
        self.application.add_handler(CommandHandler("start", self.start))
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.echo))

    def _setup_db(self):
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            join_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        self.conn.commit()

    # === Handlers ===
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        self.cursor.execute(
            'INSERT OR IGNORE INTO users(user_id, username, first_name) VALUES (?, ?, ?)',
            (user.id, user.username, user.first_name)
        )
        self.conn.commit()
        await update.message.reply_text(f"👋 مرحباً {user.first_name}! أنا بوت تجريبي.")

    async def echo(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text(f"لقد قلت: {update.message.text}")

    # === Lifecycle ===
    async def initialize(self):
        logger.info("Initializing Telegram Application...")
        await self.application.initialize()
        await self.application.start()
        logger.info("Telegram Application initialized and started.")

    async def shutdown(self):
        logger.info("Stopping Telegram Application...")
        try:
            await self.application.bot.delete_webhook()
            await self.application.stop()
            await self.application.shutdown()
            logger.info("Bot stopped and shutdown successfully.")
        except Exception as e:
            logger.exception("Error while shutting down bot: %s", e)
