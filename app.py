# app.py
import os
import logging
import asyncio
from aiohttp import web
from telegram import Update
from bot import AdvancedBot   # أو production_bot import AdvancedBot حسب اسم ملفك

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

PORT = int(os.environ.get("PORT", 10000))
TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
WEBHOOK_URL = os.environ.get("WEBHOOK_URL")  # e.g. https://your-app.onrender.com

if not TOKEN:
    raise RuntimeError("TELEGRAM_BOT_TOKEN غير موجود في المتغيرات البيئية")

if not WEBHOOK_URL:
    logger.warning("WEBHOOK_URL غير مضبوطة. ستحتاج لضبطها لتعيين webhook للـ Telegram")

# أنشئ كائن البوت (لا تقوم بتهيئته بعد)
bot = AdvancedBot(TOKEN)
app = web.Application()

# Route: health
async def health(request):
    return web.json_response({"status": "healthy"})

# Route: webhook receiver
async def webhook_handler(request):
    try:
        data = await request.json()
        update = Update.de_json(data, bot.application.bot)
        # process_update هو coroutine -> ننتظر تنفيذه داخل نفس loop
        await bot.application.process_update(update)
        return web.json_response({"ok": True})
    except Exception as e:
        logger.exception("خطأ في معالجة webhook: %s", e)
        return web.json_response({"ok": False, "error": str(e)}, status=500)

# startup/shutdown hooks
async def on_startup(app_):
    logger.info("on_startup: initializing bot...")
    await bot.initialize()
    # ضبط الويبهوك عند startup (إذا تم تحديد WEBHOOK_URL)
    if WEBHOOK_URL:
        webhook_target = f"{WEBHOOK_URL}/webhook/{TOKEN}"
        try:
            await bot.application.bot.set_webhook(webhook_target)
            logger.info("Webhook set -> %s", webhook_target)
        except Exception as e:
            logger.exception("فشل في set_webhook: %s", e)

async def on_shutdown(app_):
    logger.info("on_shutdown: stopping bot...")
    await bot.shutdown()

# ربط المسارات
app.router.add_get("/health", health)
app.router.add_post(f"/webhook/{TOKEN}", webhook_handler)
app.router.add_get("/", lambda req: web.Response(text="🤖 البوت يعمل!"))

# تسجيل hooks
app.on_startup.append(on_startup)
app.on_shutdown.append(on_shutdown)

if __name__ == "__main__":
    web.run_app(app, host="0.0.0.0", port=PORT)
