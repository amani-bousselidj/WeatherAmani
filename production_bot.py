# 📁 ai_bot.py
import os
import logging
import sqlite3
import httpx
from datetime import datetime
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes
)
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO)

class بوت_الذكاء_الاصطناعي:
    def __init__(self):
        self.token = os.getenv("TELEGRAM_BOT_TOKEN")
        self.hf_key = os.getenv("HF_API_KEY")
        self.hf_model = os.getenv("HF_MODEL", "gpt2-medium")  # يمكن تغيير النموذج

        if not self.token or not self.hf_key:
            raise ValueError("❌ التوكنات المطلوبة غير موجودة! تأكد من وجود TELEGRAM_BOT_TOKEN و HF_API_KEY")

        self.application = Application.builder().token(self.token).build()
        self.إعداد_قاعدة_بيانات_الذكاء()
        self.إعداد_معالجات_الذكاء()
        logging.info("🧠 بوت الذكاء الاصطناعي جاهز!")

    # ------------------------ إعداد قاعدة البيانات ------------------------
    def إعداد_قاعدة_بيانات_الذكاء(self):
        self.conn = sqlite3.connect("ai_bot.db", check_same_thread=False)
        self.cursor = self.conn.cursor()
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS محادثات_الذكاء (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                role TEXT,
                content TEXT,
                tokens_used INTEGER,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                model_used TEXT
            )
        """)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS إحصائيات_الذكاء (
                user_id INTEGER PRIMARY KEY,
                total_tokens INTEGER DEFAULT 0,
                total_requests INTEGER DEFAULT 0,
                last_request TIMESTAMP,
                daily_budget INTEGER DEFAULT 10000
            )
        """)
        self.conn.commit()

    # ------------------------ إعداد المعالجات ------------------------
    def إعداد_معالجات_الذكاء(self):
        self.application.add_handler(CommandHandler("ai", self.محادثة_ذكية))
        self.application.add_handler(CommandHandler("ask", self.سؤال_ذكي))
        self.application.add_handler(CommandHandler("clear", self.مسح_المحادثة))
        self.application.add_handler(CommandHandler("ai_stats", self.إحصائيات_الذكاء))
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.معالجة_رسالة_ذكية))

    # ------------------------ أوامر المستخدم ------------------------
    async def محادثة_ذكية(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        if not context.args:
            await update.message.reply_text(
                "🧠 **وضع المحادثة الذكية**\n\n"
                "اكتب /ai متبوعاً بسؤالك:\n"
                "مثال: /ai كيف أتعلم البرمجة؟"
            )
            return
        السؤال = " ".join(context.args)
        await self.معالجة_طلب_ذكاء_اصطناعي(update, السؤال, user_id)

    async def سؤال_ذكي(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        if not context.args:
            await update.message.reply_text("🤔 استخدم: /ask سؤالك هنا")
            return
        السؤال = " ".join(context.args)
        await self.معالجة_طلب_ذكاء_اصطناعي(update, السؤال, user_id, وضع="سؤال")

    async def معالجة_رسالة_ذكية(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        الرسالة = update.message.text
        if len(الرسالة) < 3 or any(كلمة in الرسالة for كلمة in ["مرحبا", "اهلا", "شكرا", "hello", "hi"]):
            return
        await self.معالجة_طلب_ذكاء_اصطناعي(update, الرسالة, user_id, وضع="محادثة")

    async def مسح_المحادثة(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        self.cursor.execute("DELETE FROM محادثات_الذكاء WHERE user_id = ?", (user_id,))
        self.conn.commit()
        await update.message.reply_text("🗑️ تم مسح جميع المحادثات السابقة.")

    async def إحصائيات_الذكاء(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        self.cursor.execute("SELECT total_tokens, total_requests, daily_budget, last_request FROM إحصائيات_الذكاء WHERE user_id = ?", (user_id,))
        result = self.cursor.fetchone()
        if result:
            total_tokens, total_requests, daily_budget, last_request = result
            متبقي = max(0, daily_budget - total_tokens)
            msg = f"""
📈 **إحصائياتك:**
💬 الطلبات: {total_requests}
🔤 الرموز: {total_tokens}
💎 الميزانية اليومية: {daily_budget}
⏳ المتبقي: {متبقي}
📅 آخر طلب: {last_request[:16] if last_request else "لا يوجد"}
"""
        else:
            msg = "📊 لم تستخدم الذكاء الاصطناعي بعد!"
        await update.message.reply_text(msg)

    # ------------------------ معالجة طلب الذكاء ------------------------
    async def معالجة_طلب_ذكاء_اصطناعي(self, update: Update, السؤال: str, user_id: int, وضع="محادثة"):
        if not self.التحقق_من_الميزانية(user_id):
            await update.message.reply_text("⏰ لقد وصلت إلى الحد اليومي. حاول لاحقًا.")
            return
        await update.message.chat.send_action(action="typing")
        try:
            سجل_المحادثة = self.جلب_سجل_المحادثة(user_id)
            الرد, tokens_used = await self.إرسال_طلب_hf(السؤال, سجل_المحادثة, وضع)
            if الرد:
                self.حفظ_المحادثة(user_id, "user", السؤال, tokens_used["prompt"])
                self.حفظ_المحادثة(user_id, "assistant", الرد, tokens_used["completion"])
                self.تحديث_إحصائيات_الذكاء(user_id, tokens_used["total"])
                await self.إرسال_رد_ذكي(update, الرد)
            else:
                await update.message.reply_text("❌ لم أتمكن من معالجة طلبك.")
        except Exception as e:
            logging.error(f"خطأ في الذكاء الاصطناعي: {e}")
            await update.message.reply_text("⚠️ حدث خطأ غير متوقع. حاول لاحقًا.")

    async def إرسال_طلب_hf(self, السؤال: str, سجل_المحادثة: list, وضع: str):
        try:
            context_text = "\n".join([f"{item['role']}: {item['content']}" for item in سجل_المحادثة])
            prompt = f"{context_text}\nUser: {السؤال}\nAssistant:"
            headers = {"Authorization": f"Bearer {self.hf_key}", "Content-Type": "application/json"}
            data = {"inputs": prompt, "parameters": {"max_new_tokens": 300, "temperature": 0.7}}
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.post(f"https://api-inference.huggingface.co/models/{self.hf_model}",
                             headers=headers, json=data)

                if response.status_code == 200:
                    result = response.json()
                    text = result[0]["generated_text"] if isinstance(result, list) else str(result)
                    الرد = text.replace(prompt, "").strip()
                    tokens_used = {"prompt": len(prompt), "completion": len(الرد), "total": len(prompt)+len(الرد)}
                    return الرد, tokens_used
                else:
                    logging.error(f"HF API error: {response.status_code} - {response.text}")
                    return None, {"prompt":0, "completion":0, "total":0}
        except Exception as e:
            logging.error(f"خطأ في طلب HF: {e}")
            return None, {"prompt":0, "completion":0, "total":0}

    # ------------------------ دوال مساعدة ------------------------
    def جلب_سجل_المحادثة(self, user_id: int, limit: int = 10):
        try:
            self.cursor.execute("""
                SELECT role, content FROM محادثات_الذكاء WHERE user_id = ?
                ORDER BY timestamp DESC LIMIT ?
            """, (user_id, limit*2))
            rows = self.cursor.fetchall()
            return [{"role": role, "content": content} for role, content in reversed(rows)]
        except Exception as e:
            logging.error(f"خطأ في جلب السجل: {e}")
            return []

    def حفظ_المحادثة(self, user_id: int, role: str, content: str, tokens: int):
        try:
            self.cursor.execute("""
                INSERT INTO محادثات_الذكاء (user_id, role, content, tokens_used, model_used)
                VALUES (?, ?, ?, ?, ?)
            """, (user_id, role, content, tokens, self.hf_model))
            self.conn.commit()
        except Exception as e:
            logging.error(f"خطأ في حفظ المحادثة: {e}")

    def تحديث_إحصائيات_الذكاء(self, user_id: int, tokens_used: int):
        try:
            self.cursor.execute("""
                INSERT INTO إحصائيات_الذكاء (user_id, total_tokens, total_requests, last_request)
                VALUES (?, ?, 1, CURRENT_TIMESTAMP)
                ON CONFLICT(user_id) DO UPDATE SET
                    total_tokens = total_tokens + ?,
                    total_requests = total_requests + 1,
                    last_request = CURRENT_TIMESTAMP
            """, (user_id, tokens_used, tokens_used))
            self.conn.commit()
        except Exception as e:
            logging.error(f"خطأ في تحديث الإحصائيات: {e}")

    def التحقق_من_الميزانية(self, user_id: int) -> bool:
        try:
            self.cursor.execute("SELECT total_tokens, daily_budget, last_request FROM إحصائيات_الذكاء WHERE user_id = ?", (user_id,))
            result = self.cursor.fetchone()
            if not result:
                self.cursor.execute("INSERT INTO إحصائيات_الذكاء (user_id, last_request) VALUES (?, CURRENT_TIMESTAMP)", (user_id,))
                self.conn.commit()
                return True
            total_tokens, daily_budget, last_request = result
            if last_request and datetime.now().date() > datetime.fromisoformat(last_request).date():
                self.cursor.execute("UPDATE إحصائيات_الذكاء SET total_tokens = 0, last_request = CURRENT_TIMESTAMP WHERE user_id = ?", (user_id,))
                self.conn.commit()
                return True
            return total_tokens < daily_budget
        except Exception as e:
            logging.error(f"خطأ في التحقق من الميزانية: {e}")
            return True

    async def إرسال_رد_ذكي(self, update: Update, الرد: str):
        if len(الرد) > 4000:
            أجزاء = [الرد[i:i + 4000] for i in range(0, len(الرد), 4000)]
            for جزء in أجزاء:
                await update.message.reply_text(جزء)
        else:
            await update.message.reply_text(الرد)

    # ------------------------ تشغيل البوت ------------------------
    def تشغيل(self):
        print("🚀 تشغيل بوت Hugging Face Telegram...")
        self.application.run_polling()


if __name__ == "__main__":
    try:
        بوت = بوت_الذكاء_الاصطناعي()
        بوت.تشغيل()
    except Exception as e:
        print(f"❌ خطأ في التشغيل: {e}")
