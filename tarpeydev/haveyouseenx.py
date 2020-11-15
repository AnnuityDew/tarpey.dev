# import native Python packages
import json
import os

# import third party packages
from flask import Blueprint, render_template, request
import numpy
import pandas
import plotly
import plotly.express as px

# import local stuff
from tarpeydev import api
from tarpeydev.db import get_dbmr
from tarpeydev.plotly_style import tarpeydev_default
from tarpeydev.users import login_required


hysx_bp = Blueprint('haveyouseenx', __name__, url_prefix='/haveyouseenx')


@hysx_bp.route('/', methods=['GET'])
@hysx_bp.route('/home', methods=['GET'])
def home():
    # read backlog and visualizations
    client = get_dbmr()
    db = client.backlogs
    stats = list(
        db.annuitydew.aggregate([
            {
                '$group': {
                    '_id': '$game_status',
                    'count': {
                        '$sum': 1
                    }
                }
            }
        ])
    )
    playtime = list(
        db.annuitydew.aggregate([
            {
                '$group': {
                    '_id': None,
                    'total_hours': {
                        '$sum': '$game_hours'
                    },
                    'total_minutes': {
                        '$sum': '$game_minutes'
                    }
                }
            }
        ])
    )
    stats = {result.get('_id'): result.get('count') for result in stats}
    playtime = int(
        playtime[0].get('total_hours') +
        playtime[0].get('total_minutes') / 60
    )
    treemap = system_treemap()

    return render_template(
        'haveyouseenx/home.html',
        stats=stats,
        playtime=playtime,
        treemap=treemap,
    )


@hysx_bp.route('/search', methods=['GET'])
def results():
    # run search
    results = api.search(request.args.get('query'), True)
    return render_template(
        'haveyouseenx/results.html',
        search_term=request.args.get('query'),
        results=results,
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
        index_col='game_id',
        encoding='latin1'
    )

    return backlog


def system_treemap():
    # read backlog and create a count column
    backlog = read_backlog()
    backlog['count'] = 1
    # column to serve as the root of the backlog
    backlog['backlog'] = 'Backlog'
    # complete gametime calc
    backlog['game_hours'] = (
        backlog['game_hours'] + (backlog['game_minutes'] / 60)
    )

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


@hysx_bp.route('/adduser', methods=['POST'])
@login_required
def create():
    return


@hysx_bp.route('/updateuser', methods=['POST', 'PUT'])
@login_required
def update():
    return


@hysx_bp.route('/deleteuser', methods=['GET', 'DELETE'])
@login_required
def delete():
    return
