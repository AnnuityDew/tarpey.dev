# import Python packages
from datetime import date
from enum import Enum
import json
from typing import List, Optional

# import third party packages
from fastapi import APIRouter, Depends
import numpy
import pandas
import plotly
import plotly.express as px
from pydantic import BaseModel, Field
from pymongo import MongoClient

# import custom local stuff
from api.db import get_dbm


hysx_api = APIRouter(
    prefix="/haveyouseenx",
    tags=["haveyouseenx"],
)


class NowPlaying(str, Enum):
    YES = "Y"
    NO = "N"


class GameStatus(str, Enum):
    NOT_STARTED = "Not Started"
    STARTED = "Started"
    BEATEN = "Beaten"
    COMPLETED = "Completed"
    MASTERED = "Mastered"
    INFINITE = "Infinite"
    WISH_LIST = "Wish List"


class PlaytimeCalc(str, Enum):
    ACTUAL = "Actual"
    ESTIMATE = "Estimate"


class BacklogGame(BaseModel):
    doc_id: int = Field(..., alias='_id')
    game_title: str
    sub_title: Optional[str]
    game_system: str
    genre: str
    now_playing: NowPlaying
    game_status: GameStatus
    game_hours: Optional[int]
    game_minutes: Optional[int]
    playtime_calc: PlaytimeCalc
    add_date: Optional[date]
    start_date: Optional[date]
    beat_date: Optional[date]
    complete_date: Optional[date]
    game_notes: Optional[str]


@hysx_api.get('/all-games')
def backlog(client: MongoClient = Depends(get_dbm)):
    db = client.backlogs
    collection = db.annuitydew
    results = list(collection.find())
    return results


@hysx_api.get('/count-by-status')
def count_by_status(client: MongoClient = Depends(get_dbm)):
    db = client.backlogs
    collection = db.annuitydew
    results = list(
        collection.aggregate([{
            '$group': {
                '_id': '$game_status',
                'count': {
                    '$sum': 1
                }
            }
        }])
    )
    stats = {result.get('_id'): result.get('count') for result in results}
    return stats


@hysx_api.get('/playtime')
def playtime(client: MongoClient = Depends(get_dbm)):
    db = client.backlogs
    collection = db.annuitydew
    results = list(
        collection.aggregate([{
            '$group': {
                '_id': None,
                'total_hours': {
                    '$sum': '$game_hours'
                },
                'total_minutes': {
                    '$sum': '$game_minutes'
                }
            }
        }])
    )
    # move chunks of 60 minutes into the hours count
    leftover_minutes = results[0].get('total_minutes') % 60
    hours_to_move = (results[0].get('total_minutes') - leftover_minutes) / 60
    results[0]['total_hours'] = results[0]['total_hours'] + hours_to_move
    results[0]['total_minutes'] = leftover_minutes

    return results[0]


@hysx_api.get('/search')
def search(client: MongoClient = Depends(get_dbm), q: Optional[str] = None):
    db = client.backlogs
    collection = db.annuitydew
    if q is None:
        results = list(collection.find())
    else:
        results = list(collection.find(
            {
                '$text': {
                    '$search': q
                }
            }
        ))

    return results


@hysx_api.get('/treemap')
def system_treemap(backlog: List[BacklogGame] = Depends(backlog)):
    # convert to pandas dataframe
    backlog = pandas.DataFrame(backlog)
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


@hysx_api.get('/bubbles')
def system_bubbles(backlog: List[BacklogGame] = Depends(backlog)):
    # convert to pandas dataframe
    backlog = pandas.DataFrame(backlog)
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

    return {
        'x_data_counts': x_data_counts,
        'y_data_dist': y_data_dist,
        'z_data_hours': z_data_hours,
        'bubble_names': bubble_names,
        'label_data': label_data,
        'color_data': color_data,
    }


@hysx_api.get('/timeline')
def timeline(backlog: List[BacklogGame] = Depends(backlog), stats=Depends(count_by_status)):
    # convert to pandas dataframe
    backlog = pandas.DataFrame(backlog)
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
    y_data_c = [int(data_point) for data_point in backlog.c.tolist()]
    y_data_b = [int(data_point) for data_point in backlog.b.tolist()]
    y_data_s = [int(data_point) for data_point in backlog.s.tolist()]
    y_data_ns = [int(data_point) for data_point in backlog.ns.tolist()]
    x_data_dates = backlog.index.tolist()
    # dates need to be converted to be JS-ready
    x_data_dates = [
        int(time_point.strftime("%s%f"))/1000 for time_point in x_data_dates
    ]

    # color data
    area_colors = px.colors.sequential.Agsunset[::2]

    return {
        'y_data_c': y_data_c,
        'y_data_b': y_data_b,
        'y_data_s': y_data_s,
        'y_data_ns': y_data_ns,
        'x_data_dates': x_data_dates,
        'area_colors': area_colors,
    }
