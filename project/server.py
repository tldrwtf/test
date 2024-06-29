from flask import Flask
import logging

from config import DATABASE
from logging_config import logger
from database import init_db
from routes.main import main
from routes.log import log_bp
from routes.search import search_bp
from routes.example import example_bp
from routes.hidden_frontend import hidden_frontend_bp

app = Flask(__name__)

# Register Blueprints
app.register_blueprint(main)
app.register_blueprint(log_bp)
app.register_blueprint(search_bp)
app.register_blueprint(example_bp)
app.register_blueprint(hidden_frontend_bp)

if __name__ == '__main__':
    init_db()
    app.run(debug=True, port=5001)