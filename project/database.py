import sqlite3
import logging

from config import DATABASE

logger = logging.getLogger(__name__)

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
                INSERT INTO requests (ip, url_params, headers, ip_info, referer) VALUES (?, ?, ?, ?, ?)
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
