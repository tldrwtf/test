from flask import Flask, request, jsonify, send_from_directory, abort, render_template_string
import sqlite3
import requests
from functools import wraps
import os
import socket
import logging
from logging.handlers import RotatingFileHandler
import colorlog
from telegram import Bot

app = Flask(__name__)
DATABASE = 'requests_log.db'
IPINFO_TOKEN = 'Your_IPInfo_token_here'
SECRET_KEY = 'your_secret_key'

WHITELISTED_IPS = ['127.0.0.1', 'localhost']
VALID_TOKENS = ['abc']

DISCORD_WEBHOOK_URL = os.getenv('DISCORD_WEBHOOK_URL')
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

# Setup logging
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

# Create handlers for Discord and Telegram if configured
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

def init_db():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ip TEXT,
            url_params TEXT,
            headers TEXT,
            ip_info TEXT,
            referer TEXT
        )
    ''')
    conn.commit()
    conn.close()
    logger.info("Database initialized.")

def log_request(ip, url_params, headers, ip_info, referer):
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()

        cursor.execute('SELECT COUNT(*) FROM requests WHERE ip = ?', (ip,))
        ip_count = cursor.fetchone()[0]

        if ip_count == 0:
            cursor.execute('''
                INSERT INTO requests (ip, url_params, headers, ip_info, referer)
                VALUES (?, ?, ?, ?, ?)
            ''', (ip, url_params, headers, ip_info, referer))
            conn.commit()
            logger.info(f"Logged request from IP: {ip}")
        else:
            logger.info(f"IP {ip} is already logged.")

        conn.close()
        return True
    except Exception as e:
        logger.error(f"Logging failed: {e}")
        return False

def log_requests(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        ip = request.headers.get('X-Forwarded-For', request.remote_addr)
        url_params = request.args.to_dict()
        headers = dict(request.headers)
        referer = request.headers.get('Referer', '')

        ip_info = {}
        if IPINFO_TOKEN:
            response = requests.get(f'https://ipinfo.io/{ip}?token={IPINFO_TOKEN}')
            if response.status_code == 200:
                ip_info = response.json()
            else:
                logger.warning(f"IPInfo request failed with status {response.status_code}")

        logging_successful = log_request(ip, str(url_params), str(headers), str(ip_info), referer)

        if not logging_successful:
            return jsonify({"status": "logging failed"}), 500

        return f(*args, **kwargs)
    return decorated_function

def access_control(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        ip = request.headers.get('X-Forwarded-For', request.remote_addr)
        token = request.headers.get('X-Access-Token')
        secret_key = request.args.get('secret_key')

        if secret_key == SECRET_KEY:
            logger.info(f"Access granted with secret key for IP: {ip}")
            return f(*args, **kwargs)

        if ip not in WHITELISTED_IPS and token not in VALID_TOKENS:
            logger.warning(f"Access denied for IP: {ip}")
            abort(403)  # Forbidden

        logger.info(f"Access granted for IP: {ip}")
        return f(*args, **kwargs)
    return decorated_function

def from_hidden_frontend(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        referer = request.headers.get('Referer')
        if referer and '/hidden_frontend/' in referer:
            return f(*args, **kwargs)
        logger.warning("Search endpoint accessed without hidden frontend referer.")
        abort(403)  # Forbidden
    return decorated_function

@app.route('/')
@access_control
def welcome():
    welcome_html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Welcome</title>
    </head>
    <body>
        <h1>Welcome to the Server</h1>
        <p>You are authorized to view this page.</p>
    </body>
    </html>
    """
    return render_template_string(welcome_html)

@app.route('/log', methods=['GET'])
@access_control
@log_requests
def log():
    return jsonify({"status": "logged"}), 200

@app.route('/search', methods=['GET'])
@access_control
@log_requests
@from_hidden_frontend
def search():
    query = request.args.get('query', '')
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT * FROM requests
        WHERE ip LIKE ? OR url_params LIKE ? OR headers LIKE ? OR ip_info LIKE ? OR referer LIKE ?
    ''', (f'%{query}%', f'%{query}%', f'%{query}%', f'%{query}%', f'%{query}%'))
    rows = cursor.fetchall()
    conn.close()

    results = []
    for row in rows:
        results.append({
            'id': row[0],
            'ip': row[1],
            'url_params': row[2],
            'headers': row[3],
            'ip_info': row[4],
            'referer': row[5]
        })

    logger.info(f"Search performed with query: {query}")
    return jsonify(results)

@app.route('/example', methods=['GET'])
@access_control
@log_requests
def example():
    logger.info("Example endpoint accessed.")
    return jsonify({"message": "This is an example endpoint."}), 200

@app.route('/hidden_frontend/<path:filename>')
@access_control
def hidden_frontend(filename):
    logger.info(f"Hidden frontend accessed with filename: {filename}")
    return send_from_directory(os.path.join(app.root_path, 'hidden_frontend'), filename)

def add_server_ip_to_whitelist():
    hostname = socket.gethostname()
    local_ip = socket.gethostbyname(hostname)
    if local_ip not in WHITELISTED_IPS:
        WHITELISTED_IPS.append(local_ip)
        logger.info(f"Added {local_ip} to the whitelist.")

if __name__ == '__main__':
    init_db()
    add_server_ip_to_whitelist()
    app.run(debug=True, port=5001)
