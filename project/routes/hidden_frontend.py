from flask import Blueprint, send_from_directory, current_app
import os
import logging

from decorators import access_control

logger = logging.getLogger(__name__)
hidden_frontend_bp = Blueprint('hidden_frontend', __name__)

@hidden_frontend_bp.route('/hidden_frontend/<path:filename>')
@access_control
def hidden_frontend(filename):
    logger.info(f"Hidden frontend accessed with filename: {filename}")
    return send_from_directory(os.path.join(current_app.root_path, 'hidden_frontend'), filename)