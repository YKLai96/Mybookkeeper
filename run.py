import os
import sys

# --- Ultimate Network Defense: Force Clear Proxies ---
os.environ.pop('HTTP_PROXY', None)
os.environ.pop('HTTPS_PROXY', None)
os.environ.pop('http_proxy', None)
os.environ.pop('https_proxy', None)

from telegram.ext import Application, MessageHandler, CallbackQueryHandler, filters
from telegram.request import HTTPXRequest
from core.config import TELEGRAM_TOKEN, GEMINI_API_KEY
from database.session import init_db
from bot.handlers import handle_photo, button_callback
from core.logger import logger


def main():
    # Print the first 8 characters to verify if the loaded Key matches your .env
    print(f"🔑 Current API Keys in use: {TELEGRAM_TOKEN[:8]}... / {GEMINI_API_KEY[:8]}...")
    
    logger.info("🛠️ Initializing local database...")
    init_db()
    
    logger.info("🔌 Connecting to Telegram servers...")
    
    # Force a longer timeout and allow auto-retry to prevent ConnectError
    req = HTTPXRequest(connect_timeout=60, read_timeout=60, write_timeout=60, pool_timeout=60)
    
    # Core: Define app and bind the custom request network settings
    app = Application.builder().token(TELEGRAM_TOKEN).request(req).build()
    
    # Register routes (Bind our handlers)
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_handler(CallbackQueryHandler(button_callback))
    
    logger.info("🚀 Enterprise AI Bookkeeper successfully started (with log daemon)")
    
    # Start polling to keep the bot online
    app.run_polling()

if __name__ == "__main__":
    main()