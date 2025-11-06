# production_bot.py
import os
import logging
import sqlite3
import schedule
import time
import threading
from datetime import datetime
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler('bot.log'), logging.StreamHandler()]
)

class TelegramAdvancedBot:
    def __init__(self):
        self.token = os.getenv("TELEGRAM_BOT_TOKEN")
        if not self.token:
            raise ValueError("❌ TELEGRAM_BOT_TOKEN مطلوب")
        
        self.application = Application.builder().token(self.token).build()
        self.setup_database()
        self.setup_handlers()
        self.start_background_tasks()
        logging.info("✅ البوت جاهز للعمل")

    def setup_database(self):
        self.conn = sqlite3.connect("bot.db", check_same_thread=False)
        self.cursor = self.conn.cursor()
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                last_name TEXT,
                join_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                message_count INTEGER DEFAULT 0
            )
        ''')
        self.conn.commit()

    def setup_handlers(self):
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("status", self.status_command))
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        await update.message.reply_text(f"مرحباً {user.first_name}!\nالبوت يعمل بنجاح.")
        self.cursor.execute(
            "INSERT OR IGNORE INTO users (user_id, username, first_name, last_name) VALUES (?, ?, ?, ?)",
            (user.id, user.username, user.first_name, user.last_name)
        )
        self.conn.commit()

    async def status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        self.cursor.execute("SELECT COUNT(*) FROM users")
        total_users = self.cursor.fetchone()[0]
        await update.message.reply_text(f"عدد المستخدمين: {total_users}")

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text("لقد استلمت رسالتك!")

    def start_background_tasks(self):
        def task():
            schedule.every(10).minutes.do(lambda: logging.info("فحص دوري"))
            while True:
                schedule.run_pending()
                time.sleep(60)
        threading.Thread(target=task, daemon=True).start()
