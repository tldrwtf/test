from flask import Blueprint, render_template_string

from decorators import access_control

main = Blueprint('main', __name__)

@main.route('/')
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