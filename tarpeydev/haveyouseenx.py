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
from tarpeydev.users import login_required


hysx_bp = Blueprint('haveyouseenx', __name__, url_prefix='/haveyouseenx')


@hysx_bp.route('/', methods=['GET'])
@hysx_bp.route('/home', methods=['GET'])
def home():
    # read backlog counts
    stats_data, response_code = api.count_by_status()
    stats = stats_data.json
    stats = {result.get('_id'): result.get('count') for result in stats}

    # read backlog total playtime
    playtime_data, response_code = api.playtime()
    playtime = playtime_data.json
    playtime = int(
        playtime[0].get('total_hours')
    )

    # create visualizations
    backlog_data, response_code = api.backlog()
    backlog_df = pandas.DataFrame(backlog_data.json)
    treemap = system_treemap(backlog_df)
    (
        x_data_counts,
        y_data_dist,
        z_data_hours,
        bubble_names,
        label_text,
        color_data
    ) = system_bubbles(backlog_df)

    return render_template(
        'haveyouseenx/home.html',
        stats=stats,
        playtime=playtime,
        treemap=treemap,
        x_data_counts=x_data_counts,
        y_data_dist=y_data_dist,
        z_data_hours=z_data_hours,
        bubble_names=bubble_names,
        label_text=label_text,
        color_data=color_data,
    )


@hysx_bp.route('/search', methods=['GET'])
def results():
    # run search
    results = api.search(request.args.get('query'))
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


def system_treemap(backlog):
    # read backlog and create a count column
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


def system_bubbles(backlog):
    # read backlog and create a count column
    backlog['count_dist'] = 1
    # complete gametime calc
    backlog['game_hours'] = (
        backlog['game_hours'] + (backlog['game_minutes'] / 60)
    )

    # pivot table by gameSystem and gameStatus.
    # fill missing values with zeroes
    system_status_df = backlog.groupby(
        by=[
            'game_system',
            'game_status',
        ]
    ).agg(
        {
            'count_dist': sum,
            'game_hours': sum,
        }
    )

    # we also want the % in each category for each system
    # this code takes care of that
    system_totals = system_status_df.groupby(['game_system']).agg({'count_dist': sum})
    normalized_df = system_status_df.div(system_totals, level='game_system')
    normalized_df['game_hours'] = system_status_df['game_hours']
    normalized_df['total_count'] = system_status_df['count_dist']

    # now reset index and prep the data for JS
    normalized_df.reset_index(inplace=True)

    # x data for each status
    x_data_counts = [
        normalized_df.loc[
            normalized_df.game_status == status
        ].total_count.tolist() for status in normalized_df.game_status.unique().tolist()
    ]

    # y data for each status
    y_data_dist = [
        normalized_df.loc[
            normalized_df.game_status == status
        ].count_dist.tolist() for status in normalized_df.game_status.unique().tolist()
    ]

    # z data for each status
    z_data_hours = [
        normalized_df.loc[
            normalized_df.game_status == status
        ].game_hours.tolist() for status in normalized_df.game_status.unique().tolist()
    ]

    # systems for each status
    label_data = [
        normalized_df.loc[
            normalized_df.game_status == status
        ].game_system.tolist() for status in normalized_df.game_status.unique().tolist()
    ]

    # categories
    bubble_names = normalized_df.game_status.unique().tolist()

    # list of hex color codes
    color_data = px.colors.qualitative.Bold

    return (
        x_data_counts, y_data_dist, z_data_hours, bubble_names, label_data, color_data
    )
