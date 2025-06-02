import asyncio
import logging
from telegram.ext import Application
from handlers import BotHandlers
from config import CONFIG

# Logging setup
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.DEBUG
)
logger = logging.getLogger(__name__)

class BotManager:
    def __init__(self):
        self.handlers = BotHandlers()

    def run(self):
        """Start the bot."""
        logger.info("🚀 Bot is running...")
        application = Application.builder().token(CONFIG["BOT_TOKEN"]).post_init(self.handlers.post_init).build()
        self.handlers.setup_handlers(application)
        application.run_polling(drop_pending_updates=True, timeout=30, allowed_updates=["message", "callback_query", "location"])

if __name__ == "__main__":
    bot = BotManager()
    asyncio.run(bot.run())