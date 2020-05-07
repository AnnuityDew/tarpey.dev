# import native Python packages
import functools

# import third party packages
from flask import Blueprint, render_template, request
import pandas


hysx_bp = Blueprint('haveyouseenx', __name__, url_prefix='/haveyouseenx')


@hysx_bp.route('/search', methods=['GET', 'POST'])
def search():
    backlog = read_backlog()
    return render_template(
        'haveyouseenx/search.html',
        df=backlog,
    )


@hysx_bp.route('/results', methods=['GET', 'POST'])
def results():
    search_term = request.form['searchterm']
    backlog = read_backlog()
    return render_template(
        'haveyouseenx/results.html',
        df=backlog,
        search_term=search_term,
    )


def read_backlog():
    backlog = pandas.read_csv(
        'tarpeydev/data/haveyouseenx/haveyouseenx_annuitydew.csv',
        index_col='id',
    ).convert_dtypes()
    
    return backlog