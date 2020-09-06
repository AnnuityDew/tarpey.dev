# import native Python packages
import functools
import io
import json
import os
import base64

# import third party packages
from flask import Blueprint, render_template, request
from matplotlib import cm, rcParams
from matplotlib.colors import Normalize
from matplotlib.figure import Figure
import numpy
import pandas
import plotly
import plotly.express as px

# import custom local stuff
from tarpeydev.plotly_style import tarpeydev_default


hysx_bp = Blueprint('haveyouseenx', __name__, url_prefix='/haveyouseenx')


@hysx_bp.route('/', methods=['GET', 'POST'])
@hysx_bp.route('/search', methods=['GET', 'POST'])
def search():
    # read backlog and visualizations
    backlog = read_backlog()
    treemap = system_treemap()

    return render_template(
        'haveyouseenx/search.html',
        df=backlog,
        treemap=treemap,
    )


@hysx_bp.route('/results', methods=['GET', 'POST'])
def results():
    search_term = request.form['search_term']
    backlog = read_backlog()
    return render_template(
        'haveyouseenx/results.html',
        df=backlog,
        search_term=search_term,
    )


def read_backlog():
    # file path
    backlog_path = os.path.join(
        os.getcwd(),
        'data',
        'haveyouseenx',
        'haveyouseenx_annuitydew.csv'
    )
    # read backlog
    backlog = pandas.read_csv(
        backlog_path,
        index_col='id',
        encoding='latin1'
    ).convert_dtypes()
    
    return backlog


def system_treemap():
    # read backlog and create a count column
    backlog = read_backlog()
    backlog['count'] = 1
    # column to serve as the root of the backlog
    backlog['backlog'] = 'Backlog'
    # complete gametime calc
    backlog['game_hours'] = backlog['game_hours'] + (backlog['game_minutes'] / 60)

    # pivot table by gameSystem and gameStatus.
    # fill missing values with zeroes

    system_status_df = backlog.groupby(
        by=[
            'backlog',
            'game_system',
            'game_status',
        ]
    ).agg(
        {
            'count': sum,
            'game_hours': sum,
        }
    ).reset_index()

    figure = px.treemap(
        system_status_df,
        path=['backlog', 'game_status', 'game_system'],
        values='count',
        color=numpy.log10(system_status_df['game_hours']),
        color_continuous_scale=px.colors.diverging.Spectral_r,
        hover_data=['game_hours'],
        template=tarpeydev_default(),
    )

    # update margins and colors
    figure.update_layout(
        margin=dict(l=10, r=0, t=10, b=10),
    )
    figure.layout.coloraxis.colorbar = dict(
        title='Hours',
        tickvals=[1.0, 2.0, 3.0],
        ticktext=[10, 100, 1000],
    )

    # convert to JSON for the web
    figure_json = json.dumps(figure, cls=plotly.utils.PlotlyJSONEncoder)

    return figure_json
