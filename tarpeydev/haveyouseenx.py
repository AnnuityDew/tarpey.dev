# import native Python packages
import json

# import third party packages
from flask import Blueprint, render_template, request
import numpy
import pandas
import plotly
import plotly.express as px

# import local stuff
from tarpeydev import api


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

    # create visualizations.
    # pass copies to the function because they each
    # do a different manipulation
    backlog_data, response_code = api.backlog()
    backlog_df = pandas.DataFrame(backlog_data.json)
    treemap = system_treemap(backlog_df.copy())

    (
        x_data_counts,
        y_data_dist,
        z_data_hours,
        bubble_names,
        label_text,
        color_data
    ) = system_bubbles(backlog_df.copy())

    (
        y_data_c, y_data_b, y_data_s, y_data_ns, x_data_dates, area_colors
    ) = timeline(backlog_df.copy(), stats)

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
        y_data_c=y_data_c,
        y_data_b=y_data_b,
        y_data_s=y_data_s,
        y_data_ns=y_data_ns,
        x_data_dates=x_data_dates,
        area_colors=area_colors,
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


def timeline(backlog, stats):
    # drop unused columns, move dates to x axis to create timeline
    # sort for most recent event at the top
    backlog = backlog.drop(
        columns=[
            'game_hours',
            'game_minutes',
            'game_notes',
            'game_status',
            'game_system',
            'genre',
            'now_playing',
            'playtime_calc',
            ]
        ).melt(
            id_vars=['_id', 'game_title', 'sub_title'],
            var_name='event_name',
            value_name='event_date',
        )

    # fill empty cells with the backlog's birth date
    backlog['event_date'] = (
        backlog['event_date'].fillna(numpy.datetime64('2011-10-08T16:00:00'))
    )

    # event date to datetime
    backlog.event_date = pandas.to_datetime(backlog.event_date, utc=True)

    # sort by date descending
    backlog.sort_values(['event_date', '_id', 'event_name'], ascending=False, inplace=True)

    # reset index
    backlog.reset_index(inplace=True)

    # next, place current status counts in the first row.
    # then we'll be able to calculate the backlog at older
    # points in time using the timeline
    backlog['not_started'] = stats.get('Not Started')
    backlog['started'] = stats.get('Started')
    backlog['beaten'] = stats.get('Beaten')
    backlog['completed'] = stats.get('Completed')
    backlog = backlog.assign(ns=0, s=0, b=0, c=0)

    # initalize modifiers
    mod_ns, mod_s, mod_b, mod_c = 0, 0, 0, 0

    for row in backlog.itertuples():
        backlog.at[row.Index, 'ns'] += mod_ns
        backlog.at[row.Index, 's'] += mod_s
        backlog.at[row.Index, 'b'] += mod_b
        backlog.at[row.Index, 'c'] += mod_c
        if row.event_name == 'add_date':
            mod_ns += 1
        elif row.event_name == 'start_date':
            mod_ns -= 1
            mod_s += 1
        elif row.event_name == 'beat_date':
            mod_s -= 1
            mod_b += 1
        elif row.event_name == 'complete_date':
            mod_b -= 1
            mod_c += 1

    # now recalculate the timeline values. this is our final data
    backlog['ns'] = backlog['not_started'] - backlog['ns']
    backlog['s'] = backlog['started'] - backlog['s']
    backlog['b'] = backlog['beaten'] - backlog['b']
    backlog['c'] = backlog['completed'] - backlog['c']

    # change sort to ascending and drop unnecessary columns
    # set index to event date
    backlog = backlog.sort_values(
        ['event_date', '_id', 'event_name'], ascending=True
    )[['event_date', 'ns', 's', 'b', 'c']]

    # drop duplicate dates (keep last, that will be most recent)
    backlog.drop_duplicates(subset=['event_date'], keep='last', inplace=True)

    # set event date as datetime index and resample to daily
    # also drop the date column (it's the index now)
    # and convert back to integers (resample changes dtype)
    time_idx = pandas.DatetimeIndex(backlog.event_date)
    backlog.set_index(time_idx, inplace=True)
    backlog = backlog.resample('D').pad().drop(
        columns='event_date'
    ).convert_dtypes()

    # limit our chart to dates after the birth of the backlog
    backlog = backlog[
        pandas.Timestamp(
            '2015-01-01 00:00:00+0000', tz='UTC', freq='D'
        ):
    ]

    # x data is time, y_data is our timeline values
    y_data_c = backlog.c.tolist()
    y_data_b = backlog.b.tolist()
    y_data_s = backlog.s.tolist()
    y_data_ns = backlog.ns.tolist()
    x_data_dates = backlog.index.tolist()
    # dates need to be converted to be JS-ready
    x_data_dates = [
        int(time_point.strftime("%s%f"))/1000 for time_point in x_data_dates
    ]

    # color data
    area_colors = px.colors.sequential.Agsunset[::2]

    return y_data_c, y_data_b, y_data_s, y_data_ns, x_data_dates, area_colors
