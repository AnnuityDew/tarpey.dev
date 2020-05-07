# import native Python packages
import functools
import random

# import third party packages
from flask import Blueprint, render_template
import pandas


index_bp = Blueprint('index', __name__, url_prefix='')


@index_bp.route('/')
def index():
    quotes = read_quotes()
    quote_id = random.randint(1, len(quotes.index))
    return render_template(
        'index/index.html',
        df=quotes,
        quote_id=quote_id,
    )


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
        'tarpeydev/data/index/index_quotes.csv',
        index_col='id',
    ).convert_dtypes()

    return quotes
