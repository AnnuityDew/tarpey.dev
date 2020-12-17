# import native Python packages

# import third party packages
from flask import Blueprint, render_template
import pandas
import seaborn

# import local stuff
from tarpeydevflask import api

index_bp = Blueprint('index', __name__, url_prefix='')


@index_bp.route('/')
def index():
    # generate color palette using Seaborn for the main site buttons
    app_colors = main_color_palette()

    return render_template(
        'index/index.html',
        colors=app_colors,
    )


def main_color_palette():
    # obtain circular palette of hex colors for the main page.
    # h = starting hue
    # l = lightness
    # s = saturation
    hex_color_list = seaborn.hls_palette(7, h=.75, l=.3, s=.7).as_hex()
    # hex_color_list = seaborn.color_palette("cubehelix", 7).as_hex()

    # add the rest of the html style formatting string to each
    hex_color_list = ["color:ffffff; background-color:" + color for color in hex_color_list]
    return hex_color_list


@index_bp.route('/colors')
def colors():
    return render_template('index/colors.html')


@index_bp.route('/links')
def links():
    return render_template('index/links.html')


@index_bp.route('/apps')
def apps():
    return render_template('index/apps.html')


@index_bp.route('/games')
def games():
    return render_template('index/games.html')


def read_quotes():
    quotes = pandas.read_csv(
        'data/index/index_quotes.csv',
        index_col='_id',
    ).convert_dtypes()

    return quotes
