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

class بوت_الذكاء_الاصطناعي:
    def __init__(self):
        self.token = os.getenv("TELEGRAM_BOT_TOKEN")
        self.hf_key = os.getenv("HF_API_KEY")
        self.hf_model = os.getenv("HF_MODEL", "gpt2-medium")  # اختر النموذج المناسب

        if not self.token or not self.hf_key:
            raise ValueError("❌ التوكنات المطلوبة غير موجودة! تأكد من وجود TELEGRAM_BOT_TOKEN و HF_API_KEY")

        self.application = Application.builder().token(self.token).build()
        self.إعداد_قاعدة_بيانات_الذكاء()
        self.إعداد_معالجات_الذكاء()
        logging.info("🧠 بوت الذكاء الاصطناعي جاهز!")

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

    def إعداد_معالجات_الذكاء(self):
        self.application.add_handler(CommandHandler("ai", self.محادثة_ذكية))
        self.application.add_handler(CommandHandler("ask", self.سؤال_ذكي))
        self.application.add_handler(CommandHandler("clear", self.مسح_المحادثة))
        self.application.add_handler(CommandHandler("ai_stats", self.إحصائيات_الذكاء))
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.معالجة_رسالة_ذكية))

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
                await self.إرسال_رد_ذكي(update, الرد, tokens_used)
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
            payload = {
                "model": self.hf_model,
                "inputs": prompt,
                "parameters": {"max_new_tokens": 300, "temperature": 0.7}
            }
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.post("https://router.huggingface.co/hf-inference",
                                             headers=headers, json=payload)
                if response.status_code == 200:
                    result = response.json()
                    # استخراج النص من الحقل المناسب
                    if "generated_text" in result:
                        الرد = result["generated_text"].replace(prompt, "").strip()
                    elif "outputs" in result and len(result["outputs"]) > 0:
                        الرد = result["outputs"][0].get("generated_text", "").replace(prompt, "").strip()
                    else:
                        الرد = ""
                    tokens_used = {"prompt": len(prompt), "completion": len(الرد), "total": len(prompt)+len(الرد)}
                    return الرد, tokens_used
                else:
                    logging.error(f"HF Router API error: {response.status_code} - {response.text}")
                    return None, {"prompt": 0, "completion": 0, "total": 0}
        except Exception as e:
            logging.error(f"خطأ في طلب HF Router: {e}")
            return None, {"prompt": 0, "completion": 0, "total": 0}

    # بقية الدوال كما هي: بناء_رسالة_النظام، جلب_سجل_المحادثة، حفظ_المحادثة، تحديث_إحصائيات_الذكاء، التحقق_من_الميزانية، إرسال_رد_ذكي، مسح_المحادثة، إحصائيات_الذكاء

    def تشغيل(self):
        print("🚀 تشغيل بوت Hugging Face Telegram مع Router API...")
        self.application.run_polling()


if __name__ == "__main__":
    try:
        بوت = بوت_الذكاء_الاصطناعي()
        بوت.تشغيل()
    except Exception as e:
        print(f"❌ خطأ في التشغيل: {e}")
