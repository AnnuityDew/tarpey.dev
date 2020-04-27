# import native Python packages
import functools

# import third party packages
from flask import Blueprint, render_template

bp = Blueprint('index', __name__, url_prefix='')

@bp.route('/')
def index():
    return render_template('index/index.html')

@bp.route('/colors')
def colors():
    return render_template('index/colors.html')

@bp.route('/links')
def links():
    return render_template('index/links.html')

@bp.route('/apps')
def apps():
    return render_template('index/apps.html')

@bp.route('/games')
def games():
    return render_template('index/games.html')
