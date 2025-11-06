# 📁 app.py
import os
import logging
from aiohttp import web
from telegram import Update
from production_bot import بوت_الذكاء_الاصطناعي

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# تحميل المتغيرات
PORT = int(os.environ.get("PORT", 10000))
TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
WEBHOOK_URL = os.environ.get("WEBHOOK_URL")

# تأكيد وجود البيانات الأساسية
if not TOKEN:
    raise RuntimeError("❌ TELEGRAM_BOT_TOKEN غير موجود في .env")
if not WEBHOOK_URL:
    raise RuntimeError("❌ WEBHOOK_URL غير موجود في .env")

# إنشاء كائن البوت
bot_instance = بوت_الذكاء_الاصطناعي()
app = web.Application()

# ✅ نقطة اختبار
async def health(request):
    return web.json_response({"status": "healthy", "bot": "AI Telegram Bot"})

# ✅ Webhook endpoint
async def webhook_handler(request):
    try:
        data = await request.json()
        update = Update.de_json(data, bot_instance.application.bot)
        await bot_instance.application.process_update(update)
        return web.json_response({"ok": True})
    except Exception as e:
        logger.exception("❌ خطأ في webhook: %s", e)
        return web.json_response({"ok": False, "error": str(e)}, status=500)

# ✅ تشغيل عند بدء التشغيل
async def on_startup(app_):
    logger.info("🚀 بدء تشغيل البوت...")
    await bot_instance.application.initialize()
    webhook_target = f"{WEBHOOK_URL}/webhook/{TOKEN}"
    await bot_instance.application.bot.set_webhook(webhook_target)
    logger.info(f"✅ تم ضبط الـ Webhook على: {webhook_target}")

# ✅ عند الإيقاف
async def on_shutdown(app_):
    logger.info("🛑 إيقاف البوت...")
    await bot_instance.application.shutdown()

# ✅ ربط المسارات
app.router.add_get("/", lambda req: web.Response(text="🤖 البوت يعمل!"))
app.router.add_get("/health", health)
app.router.add_post(f"/webhook/{TOKEN}", webhook_handler)

app.on_startup.append(on_startup)
app.on_shutdown.append(on_shutdown)

if __name__ == "__main__":
    web.run_app(app, host="0.0.0.0", port=PORT)
