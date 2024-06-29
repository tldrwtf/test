import logging
from logging.handlers import RotatingFileHandler
import colorlog
import requests
from config import DISCORD_WEBHOOK_URL, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
from telegram import Bot

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Create a rotating file handler
rotating_file_handler = RotatingFileHandler('server.log', maxBytes=1000000, backupCount=5)
rotating_file_handler.setLevel(logging.INFO)
file_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
rotating_file_handler.setFormatter(file_formatter)

# Create a console handler with colorlog
console_handler = colorlog.StreamHandler()
console_handler.setLevel(logging.INFO)
console_formatter = colorlog.ColoredFormatter(
    '%(log_color)s%(asctime)s - %(levelname)s - %(message)s',
    log_colors={
        'DEBUG': 'white',
        'INFO': 'green',
        'WARNING': 'yellow',
        'ERROR': 'red',
        'CRITICAL': 'bold_red',
    }
)
console_handler.setFormatter(console_formatter)

# Add the file and console handlers to the logger
logger.addHandler(rotating_file_handler)
logger.addHandler(console_handler)

if DISCORD_WEBHOOK_URL:
    class DiscordHandler(logging.Handler):
        def emit(self, record):
            log_entry = self.format(record)
            payload = {'content': log_entry}
            requests.post(DISCORD_WEBHOOK_URL, json=payload)

    discord_handler = DiscordHandler()
    discord_handler.setLevel(logging.INFO)
    discord_handler.setFormatter(file_formatter)
    logger.addHandler(discord_handler)

if TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID:
    class TelegramHandler(logging.Handler):
        def __init__(self, bot_token, chat_id):
            super().__init__()
            self.bot = Bot(token=bot_token)
            self.chat_id = chat_id
    
        def emit(self, record):
            log_entry = self.format(record)
            self.bot.send_message(chat_id=self.chat_id, text=log_entry)
    
    telegram_handler = TelegramHandler(TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID)
    telegram_handler.setLevel(logging.INFO)
    telegram_handler.setFormatter(file_formatter)
    logger.addHandler(telegram_handler)