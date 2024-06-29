import os
from dotenv import load_dotenv
load_dotenv()

DATABASE = os.getenv('DATABASE')
IPINFO_TOKEN = os.getenv('IPINFO_TOKEN')
SECRET_KEY = os.getenv('SECRET_KEY')
VALID_TOKENS = os.getenv('VALID_TOKENS').split(',')
DISCORD_WEBHOOK_URL = os.getenv('DISCORD_WEBHOOK_URL')
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
