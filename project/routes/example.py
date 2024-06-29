from flask import Blueprint, jsonify
import logging

from decorators import access_control, log_requests

example_bp = Blueprint('example', __name__)

logger = logging.getLogger(__name__)

@example_bp.route('/example', methods=['GET'])
@access_control
@log_requests
def example():
    logger.info("Example endpoint accessed.")
    return jsonify({"message": "This is an example endpoint."}), 200