from flask import Blueprint, request, jsonify
import sqlite3
import logging

from decorators import access_control, log_requests, from_hidden_frontend
from config import DATABASE

logger = logging.getLogger(__name__)
search_bp = Blueprint('search', __name__)

@search_bp.route('/search', methods=['GET'])
@access_control
@log_requests
@from_hidden_frontend

def search():
    query = request.args.get('query', '')
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT * FROM requests WHERE ip LIKE ? OR url_params LIKE ? OR headers LIKE ? OR ip_info LIKE ? OR referer LIKE ?
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