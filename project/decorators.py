from functools import wraps
from flask import request, jsonify, abort, redirect
import logging
import requests

from config import IPINFO_TOKEN, SECRET_KEY, VALID_TOKENS
from database import log_request

logger = logging.getLogger(__name__)

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
            logger.warning(f"IPInfo request failed with status{response.status_code}")
        
        logging_successful = log_request(ip, str(url_params), str(headers), str(ip_info), referer)
        if not logging_successful: 
            return jsonify({"status": "logging failed"}), 500
# Redirection logic
        if 'redirect' in url_params:
            redirect_param = url_params['redirect']
            redirect_urls = {
                'param1': 'https://example.com/page1',
                'param2': 'https://example.com/page2',
                'param3': 'https://example.com/page3',
# Add more mappings as needed
            }
            if redirect_param in redirect_urls:
                return redirect(redirect_urls[redirect_param])
        return f(*args, **kwargs)
    return decorated_function

def access_control(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = request.headers.get('X-Access-Token')
        secret_key = request.args.get('SECRET_KEY')

        if secret_key == SECRET_KEY:
            logger.info(f"Access granted with secret key.")
            return f(*args, **kwargs)
        if token not in VALID_TOKENS:
            logger.warning(f"Access denied.")
            abort(403) # Forbidden

        logger.info(f"Access granted.")
        return f(*args, **kwargs)
    return decorated_function

def from_hidden_frontend(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        referer = request.headers.get('Referer')
        if referer and '/hidden_frontend/' in referer:
            return f(*args, **kwargs)
        logger.warning("Search endpoint accessed without hidden frontend referer.")
        abort(403) # Forbidden
    return decorated_function