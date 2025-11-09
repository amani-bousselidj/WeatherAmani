# 📁 ai_bot.py
import os
import logging
import sqlite3
import requests
import json
import base64
from datetime import datetime, timedelta
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler
# from dotenv import load_dotenv

print("TELEGRAM_BOT_TOKEN:", os.getenv("TELEGRAM_BOT_TOKEN"))
print("GROQ_API_KEY:", os.getenv("GROQ_API_KEY"))
load_dotenv()

class بوت_الذكاء_الاصطناعي:
    def __init__(self):
        self.token = os.getenv('TELEGRAM_BOT_TOKEN')
        self.grok_key = os.getenv('GROK_API_KEY')
        self.grok_model = os.getenv('GROK_MODEL', 'grok-beta')

        
        if not self.token or not self.grok_key:
            raise ValueError("❌ التوكنات المطلوبة غير موجودة!")
        
        self.application = Application.builder().token(self.token).build()
        self.إعداد_قاعدة_بيانات_الذكاء()
        self.إعداد_معالجات_الذكاء()
        
        logging.info("🧠 بوت الذكاء الاصطناعي جاهز!")
    
    def إعداد_قاعدة_بيانات_الذكاء(self):
        """إنشاء قاعدة بيانات للمحادثات الذكية"""
        self.conn = sqlite3.connect('ai_bot.db', check_same_thread=False)
        self.cursor = self.conn.cursor()
        
        # جدول محادثات الذكاء الاصطناعي
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS محادثات_الذكاء (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                role TEXT,
                content TEXT,
                tokens_used INTEGER,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                model_used TEXT
            )
        ''')
        
        # جدول إحصائيات الذكاء الاصطناعي
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS إحصائيات_الذكاء (
                user_id INTEGER PRIMARY KEY,
                total_tokens INTEGER DEFAULT 0,
                total_requests INTEGER DEFAULT 0,
                last_request TIMESTAMP,
                daily_budget INTEGER DEFAULT 10000  # حدود استهلاك يومية
            )
        ''')
        
        self.conn.commit()
    
    def إعداد_معالجات_الذكاء(self):
        """إعداد معالجات الأوامر الذكية"""
        # أوامر الذكاء الاصطناعي
        self.application.add_handler(CommandHandler("ai", self.محادثة_ذكية))
        self.application.add_handler(CommandHandler("ask", self.سؤال_ذكي))
        self.application.add_handler(CommandHandler("clear", self.مسح_المحادثة))
        self.application.add_handler(CommandHandler("ai_stats", self.إحصائيات_الذكاء))
        
        # محادثة تفاعلية مع الذكاء الاصطناعي
        self.application.add_handler(MessageHandler(
            filters.TEXT & ~filters.COMMAND, 
            self.معالجة_رسالة_ذكية
        ))
        
        # معالجة الصور (لرؤية الكمبيوتر)
        self.application.add_handler(MessageHandler(
            filters.PHOTO, 
            self.معالجة_صورة
        ))
    
    async def محادثة_ذكية(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """بدء محادثة ذكية مع ChatGPT"""
        user_id = update.effective_user.id
        
        if not context.args:
            await update.message.reply_text(
                "🧠 **وضع المحادثة الذكية**\n\n"
                "اكتب /ai متبوعاً بسؤالك أو رسالتك:\n"
                "مثال: /ai كيف أتعلم البرمجة؟\n\n"
                "💡 يمكنك أيضاً محادثتي مباشرة!"
            )
            return
        
        السؤال = ' '.join(context.args)
        await self.معالجة_طلب_ذكاء_اصطناعي(update, السؤال, user_id)
    
    async def سؤال_ذكي(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """سؤال مباشر للذكاء الاصطناعي"""
        user_id = update.effective_user.id
        
        if not context.args:
            await update.message.reply_text(
                "🤔 **اسألني أي شيء!**\n\n"
                "استخدم: /ask سؤالك هنا\n"
                "مثال: /ask اشرح نظرية النسبية"
            )
            return
        
        السؤال = ' '.join(context.args)
        await self.معالجة_طلب_ذكاء_اصطناعي(update, السؤال, user_id, وضع="سؤال")
    
    async def معالجة_رسالة_ذكية(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """معالجة الرسائل العادية بالذكاء الاصطناعي"""
        user_id = update.effective_user.id
        الرسالة = update.message.text
        
        # تجاهل الرسائل القصيرة جداً أو التحيات البسيطة
        if len(الرسالة) < 3 or any(كلمة in الرسالة for كلمة in ['مرحبا', 'اهلا', 'شكرا', 'hello', 'hi']):
            return
        
        # استخدام الذكاء الاصطناعي للرد الذكي
        await self.معالجة_طلب_ذكاء_اصطناعي(update, الرسالة, user_id, وضع="محادثة")
    
    async def معالجة_طلب_ذكاء_اصطناعي(self, update: Update, السؤال: str, user_id: int, وضع="محادثة"):
        """معالجة طلبات الذكاء الاصطناعي مع إدارة التكلفة"""
        
        # التحقق من الميزانية اليومية
        if not self.التحقق_من_الميزانية(user_id):
            await update.message.reply_text(
                "⏰ **وصلت للحد اليومي**\n\n"
                "لقد استخدمت الحد اليومي من طلبات الذكاء الاصطناعي.\n"
                "يمكنك المحاولة مرة أخرى غداً أو استخدام /ai_stats لمشاهدة الإحصائيات."
            )
            return
        
        # عرض مؤشر الكتابة
        await update.message.chat.send_action(action="typing")
        
        try:
            # جلب سجل المحادثة
            سجل_المحادثة = self.جلب_سجل_المحادثة(user_id)
            
            # إرسال الطلب إلى OpenAI
            الرد, tokens_used = await self.إرسال_طلب_grok(السؤال, سجل_المحادثة, وضع) 
            if الرد:
                # حفظ المحادثة في قاعدة البيانات
                self.حفظ_المحادثة(user_id, "user", السؤال, tokens_used['prompt'])
                self.حفظ_المحادثة(user_id, "assistant", الرد, tokens_used['completion'])
                
                # تحديث الإحصائيات
                self.تحديث_إحصائيات_الذكاء(user_id, sum(tokens_used.values()))
                
                # إرسال الرد مع تنسيق جميل
                await self.إرسال_رد_ذكي(update, الرد, tokens_used)
            else:
                await update.message.reply_text(
                    "❌ **عذراً، لم أتمكن من معالجة طلبك**\n\n"
                    "قد يكون هناك مشكلة في الاتصال أو تجاوز للحد المسموح.\n"
                    "حاول مرة أخرى بعد قليل."
                )
                
        except Exception as e:
            logging.error(f"خطأ في الذكاء الاصطناعي: {e}")
            await update.message.reply_text(
                "⚠️ **حدث خطأ غير متوقع**\n\n"
                "يعذر النظام حالياً، يرجى المحاولة لاحقاً."
            )
    
    def التحقق_من_الميزانية(self, user_id: int) -> bool:
        """التحقق من أن المستخدم لم يتجاوز الميزانية اليومية"""
        try:
            self.cursor.execute('''
                SELECT total_tokens, daily_budget, last_request 
                FROM إحصائيات_الذكاء WHERE user_id = ?
            ''', (user_id,))
            
            result = self.cursor.fetchone()
            
            if not result:
                # مستخدم جديد - إنشاء سجل
                self.cursor.execute('''
                    INSERT INTO إحصائيات_الذكاء (user_id, last_request) 
                    VALUES (?, CURRENT_TIMESTAMP)
                ''', (user_id,))
                self.conn.commit()
                return True
            
            total_tokens, daily_budget, last_request = result
            
            # إعادة تعيين الميزانية اليومية إذا كان اليوم الجديد
            if last_request and datetime.now().date() > datetime.fromisoformat(last_request).date():
                self.cursor.execute('''
                    UPDATE إحصائيات_الذكاء 
                    SET total_tokens = 0, last_request = CURRENT_TIMESTAMP 
                    WHERE user_id = ?
                ''', (user_id,))
                self.conn.commit()
                return True
            
            return total_tokens < daily_budget
            
        except Exception as e:
            logging.error(f"خطأ في التحقق من الميزانية: {e}")
            return True  # السماح بالاستخدام في حالة الخطأ
    
    def جلب_سجل_المحادثة(self, user_id: int, limit: int = 10):
        """جلب سجل المحادثة الأخير للمستخدم"""
        try:
            self.cursor.execute('''
                SELECT role, content 
                FROM محادثات_الذكاء 
                WHERE user_id = ? 
                ORDER BY timestamp DESC 
                LIMIT ?
            ''', (user_id, limit * 2))  # ضعف الحد لضمان محادثة متوازنة
            
            rows = self.cursor.fetchall()
            سجل = []
            
            for role, content in reversed(rows):
                سجل.append({"role": role, "content": content})
            
            return سجل
            
        except Exception as e:
            logging.error(f"خطأ في جلب سجل المحادثة: {e}")
            return []
    
    async def إرسال_طلب_grok(self, السؤال: str, سجل_المحادثة: list, وضع: str):
        """إرسال طلب إلى Grok API من xAI"""
        try:
            رسائل_النظام = self.بناء_رسالة_النظام(وضع)
            محادثة = [{"role": "system", "content": رسائل_النظام}]
            محادثة.extend(سجل_المحادثة)
            محادثة.append({"role": "user", "content": السؤال})

            headers = {
                "Authorization": f"Bearer {self.grok_key}",
                "Content-Type": "application/json"
            }

            data = {
                "model": self.grok_model,
                "messages": محادثة,
                "max_tokens": 1000,
                "temperature": 0.7
            }

            response = requests.post(
                "https://api.x.ai/v1/chat/completions",
                headers=headers,
                json=data,
                timeout=30
            )

            if response.status_code == 200:
                result = response.json()
                الرد = result['choices'][0]['message']['content']

                tokens_used = {
                    'prompt': result.get('usage', {}).get('prompt_tokens', 0),
                    'completion': result.get('usage', {}).get('completion_tokens', 0),
                    'total': result.get('usage', {}).get('total_tokens', 0)
                }

                return الرد, tokens_used
            else:
                logging.error(f"Grok API error: {response.status_code} - {response.text}")
                return None, None

        except Exception as e:
            logging.error(f"خطأ في طلب Grok: {e}")
            return None, None

    def بناء_رسالة_النظام(self, وضع: str) -> str:
        """بناء رسالة النظام بناءً على الوضع"""
        if وضع == "سؤال":
            return """
            أنا مساعد ذكي متخصص في الإجابة على الأسئلة بدقة ووضوح.
            أقدم إجابات مباشرة ومفيدة مع أمثلة عندما يكون ذلك مناسباً.
            أستخدم لغة عربية فصحى واضحة.
            أكون دقيقاً في المعلومات وأعترف عندما لا أعرف شيئاً.
            """
        else:  # محادثة عادية
            return """
            أنا مساعد ذكي ودود أتحدث باللغة العربية.
            أكون مفيداً، ودوداً، ودقيقاً في إجاباتي.
            أستخدم لغة عربية واضحة ومناسبة للمحادثة.
            أقدم معلومات مفيدة وأعترف عندما لا أعرف إجابة.
            أحافظ على إجاباتي معقولة الطول ومناسبة للمحادثة.
            """
    
    def حفظ_المحادثة(self, user_id: int, role: str, content: str, tokens: int):
        """حفظ رسالة في سجل المحادثة"""
        try:
            self.cursor.execute('''
                INSERT INTO محادثات_الذكاء 
                (user_id, role, content, tokens_used, model_used) 
                VALUES (?, ?, ?, ?, ?)
            ''', (user_id, role, content, tokens, self.grok_model))
            
            self.conn.commit()
        except Exception as e:
            logging.error(f"خطأ في حفظ المحادثة: {e}")
    
    def تحديث_إحصائيات_الذكاء(self, user_id: int, tokens_used: int):
        """تحديث إحصائيات استخدام الذكاء الاصطناعي"""
        try:
            self.cursor.execute('''
                INSERT INTO إحصائيات_الذكاء (user_id, total_tokens, total_requests, last_request)
                VALUES (?, ?, 1, CURRENT_TIMESTAMP)
                ON CONFLICT(user_id) DO UPDATE SET
                total_tokens = total_tokens + ?,
                total_requests = total_requests + 1,
                last_request = CURRENT_TIMESTAMP
            ''', (user_id, tokens_used, tokens_used))
            
            self.conn.commit()
        except Exception as e:
            logging.error(f"خطأ في تحديث إحصائيات الذكاء: {e}")
    
    async def إرسال_رد_ذكي(self, update: Update, الرد: str, tokens_used: dict):
        """إرسال الرد مع تنسيق جميل ومعلومات الاستخدام"""
        # تقسيم الرد إذا كان طويلاً جداً (حد تليجرام 4096 حرف)
        if len(الرد) > 4000:
            أجزاء = [الرد[i:i+4000] for i in range(0, len(الرد), 4000)]
            for جزء in أجزاء:
                await update.message.reply_text(جزء)
        else:
            await update.message.reply_text(الرد)
        
        # إرسال إحصائيات الاستخدام (للمستخدمين المتقدمين)
        if tokens_used['total'] > 500:  # فقط للطلبات الكبيرة
            رسالة_الإحصائيات = f"""
            📊 **إحصائيات الاستخدام:**
            • الرموز المستخدمة: {tokens_used['total']}
            • الميزانية المتبقية: {self.الحصول_على_الميزانية_المتبقية(update.effective_user.id)}
            """
            await update.message.reply_text(رسالة_الإحصائيات)
    
    def الحصول_على_الميزانية_المتبقية(self, user_id: int) -> str:
        """الحصول على الميزانية اليومية المتبقية"""
        try:
            self.cursor.execute('''
                SELECT daily_budget, total_tokens 
                FROM إحصائيات_الذكاء WHERE user_id = ?
            ''', (user_id,))
            
            result = self.cursor.fetchone()
            if result:
                daily_budget, total_tokens = result
                متبقي = max(0, daily_budget - total_tokens)
                return f"{متبقي} رمز"
            return "غير محدد"
        except:
            return "غير محدد"
    
    async def مسح_المحادثة(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """مسح سجل المحادثة للمستخدم"""
        user_id = update.effective_user.id
        
        try:
            self.cursor.execute('''
                DELETE FROM محادثات_الذكاء WHERE user_id = ?
            ''', (user_id,))
            
            self.conn.commit()
            
            await update.message.reply_text(
                "🗑️ **تم مسح سجل المحادثة**\n\n"
                "تم مسح جميع محادثاتك السابقة مع الذكاء الاصطناعي.\n"
                "المحادثة الجديدة ستبدأ من الصفر."
            )
            
        except Exception as e:
            logging.error(f"خطأ في مسح المحادثة: {e}")
            await update.message.reply_text("❌ حدث خطأ أثناء مسح المحادثة.")
    
    async def إحصائيات_الذكاء(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """عرض إحصائيات استخدام الذكاء الاصطناعي"""
        user_id = update.effective_user.id
        
        try:
            self.cursor.execute('''
                SELECT total_tokens, total_requests, daily_budget, last_request
                FROM إحصائيات_الذكاء WHERE user_id = ?
            ''', (user_id,))
            
            result = self.cursor.fetchone()
            
            if result:
                total_tokens, total_requests, daily_budget, last_request = result
                متبقي = max(0, daily_budget - total_tokens)
                
                رسالة_الإحصائيات = f"""
                📈 **إحصائيات الذكاء الاصطناعي**
                
                💬 الطلبات الكلية: {total_requests}
                🔤 الرموز المستخدمة: {total_tokens}
                💎 الميزانية اليومية: {daily_budget}
                ⏳ المتبقي اليوم: {متبقي}
                
                📅 آخر طلب: {last_request[:16] if last_request else 'لا يوجد'}
                
                💡 يمكنك استخدام /clear لمسح سجل المحادثة.
                """
            else:
                رسالة_الإحصائيات = """
                📈 **إحصائيات الذكاء الاصطناعي**
                
                لم تستخدم الذكاء الاصطناعي بعد!
                جرب /ai أو ابدأ محادثة عادية.
                """
            
            await update.message.reply_text(رسالة_الإحصائيات)
            
        except Exception as e:
            logging.error(f"خطأ في إحصائيات الذكاء: {e}")
            await update.message.reply_text("❌ حدث خطأ في جلب الإحصائيات.")
    
    async def معالجة_صورة(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """معالجة الصور المرفوعة (لرؤية الكمبيوتر)"""
        await update.message.reply_text(
            "🖼️ **ميزة معالجة الصور**\n\n"
            "هذه الميزة قيد التطوير حالياً!\n"
            "قريباً سأتمكن من تحليل الصور والرد عليها.\n\n"
            "💡 جرب محادثة نصية مع /ai"
        )
    
    def تشغيل(self):
        """تشغيل البوت"""
        print("🧠 بدأ تشغيل بوت الذكاء الاصطناعي...")
        self.application.run_polling()

# التشغيل الرئيسي
if __name__ == "__main__":
    try:
        بوت = بوت_الذكاء_الاصطناعي()
        بوت.تشغيل()
    except Exception as e:
        print(f"❌ خطأ في تشغيل البوت: {e}")