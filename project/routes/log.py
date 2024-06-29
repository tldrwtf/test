from flask import Blueprint, jsonify

from decorators import access_control, log_requests

log_bp = Blueprint('log', __name__)

@log_bp.route('/log', methods=['GET'])
@access_control
@log_requests
def log():
    return jsonify({"status": "logged"}), 200