# import native Python packages
import os

# import third party packages
from flask import g, redirect, url_for
from flask_swagger_ui import get_swaggerui_blueprint


if os.environ.get('FLASK_ENV') == 'development':
    json_path = 'http://127.0.0.1:5000/static/swagger.json'
else:
    json_path = 'https://tarpey.dev/static/swagger.json'

swag_bp = get_swaggerui_blueprint(
    '/swagger',
    json_path,
)


@swag_bp.before_request
def restrict_swagger():
    if g.user is None:
        return redirect(url_for('users.login'))
