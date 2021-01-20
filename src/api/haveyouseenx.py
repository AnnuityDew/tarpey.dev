# import Python packages
from datetime import datetime
from enum import Enum
import json
from typing import List, Optional

# import third party packages
from fastapi import APIRouter, Depends, HTTPException
from motor.motor_asyncio import AsyncIOMotorClient
import numpy
import pandas
import plotly
import plotly.express as px
from odmantic import AIOEngine, Field, Model, ObjectId

# import custom local stuff
from src.api.db import get_odm
from src.api.users import UserOut, oauth2_scheme


hysx_api = APIRouter(
    prefix="/haveyouseenx",
    tags=["haveyouseenx"],
)


class YesNo(str, Enum):
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


class BacklogGame(Model):
    game_title: str
    sub_title: Optional[str]
    game_system: str
    genre: str
    dlc: YesNo
    now_playing: YesNo
    game_status: GameStatus
    game_hours: Optional[int]
    game_minutes: Optional[int]
    playtime_calc: Optional[PlaytimeCalc]
    add_date: Optional[datetime]
    start_date: Optional[datetime]
    beat_date: Optional[datetime]
    complete_date: Optional[datetime]
    game_notes: Optional[str]


class BacklogGamePatch(Model):
    game_title: Optional[str]
    sub_title: Optional[str]
    game_system: Optional[str]
    genre: Optional[str]
    dlc: Optional[YesNo]
    now_playing: Optional[YesNo]
    game_status: Optional[GameStatus]
    game_hours: Optional[int]
    game_minutes: Optional[int]
    playtime_calc: Optional[PlaytimeCalc]
    add_date: Optional[datetime]
    start_date: Optional[datetime]
    beat_date: Optional[datetime]
    complete_date: Optional[datetime]
    game_notes: Optional[str]


@hysx_api.get('/annuitydew/game/all')
async def get_all_games(client: AsyncIOMotorClient = Depends(get_odm)):
    engine = AIOEngine(motor_client=client, database="backlogs")
    data = [game async for game in engine.find(BacklogGame, sort=BacklogGame.id)]
    if data:
        return data
    else:
        raise HTTPException(status_code=404, detail="No data found!")


@hysx_api.post('/annuitydew/game')
async def add_games(
    doc_list: List[BacklogGame],
    client: AsyncIOMotorClient = Depends(get_odm),
    user: UserOut = Depends(oauth2_scheme),
):
    engine = AIOEngine(motor_client=client, database="backlogs")
    result = await engine.save_all(doc_list)
    return {
        "result": result,
    }


@hysx_api.get('/annuitydew/game/{oid}', response_model=BacklogGame)
async def get_game(
    oid: ObjectId,
    client: AsyncIOMotorClient = Depends(get_odm),
    user: UserOut = Depends(oauth2_scheme),
):
    engine = AIOEngine(motor_client=client, database="backlogs")
    game = await engine.find_one(BacklogGame, BacklogGame.id == oid)
    if game:
        return game
    else:
        raise HTTPException(status_code=404, detail="No data found!")


@hysx_api.patch('/annuitydew/game/{oid}')
async def edit_game(
    oid: ObjectId,
    patch: BacklogGamePatch,
    client: AsyncIOMotorClient = Depends(get_odm),
    user: UserOut = Depends(oauth2_scheme),
):
    engine = AIOEngine(motor_client=client, database="backlogs")
    game = await engine.find_one(BacklogGamePatch, BacklogGamePatch.id == oid)
    if game is None:
        raise HTTPException(status_code=404, detail="No data found!")

    patch_dict = patch.dict(exclude_unset=True)
    for attr, value in patch_dict.items():
        setattr(game, attr, value)
    result = await engine.save(game)

    return {
        "result": result,
    }


@hysx_api.delete('/annuitydew/game/{oid}')
async def delete_game(
    oid: ObjectId,
    client: AsyncIOMotorClient = Depends(get_odm),
    user: UserOut = Depends(oauth2_scheme),
):
    engine = AIOEngine(motor_client=client, database="backlogs")
    game = await engine.find_one(BacklogGame, BacklogGame.id == oid)
    if game is None:
        raise HTTPException(status_code=404, detail="No data found!")

    await engine.delete(game)

    return {
        "game": game,
    }


@hysx_api.get('/annuitydew/stats/counts')
async def count_by_status(client: AsyncIOMotorClient = Depends(get_odm)):
    engine = AIOEngine(motor_client=client, database="backlogs")
    collection = engine.get_collection(BacklogGame)
    results = await collection.aggregate([{
        '$group': {
            '_id': '$game_status',
            'count': {
                '$sum': 1
            }
        }
    }]).to_list(length=None)

    stats = {result.get('_id'): result.get('count') for result in results}
    sorted_stats = dict(sorted(stats.items(), key=lambda item: item[1], reverse=True))
    return sorted_stats


@hysx_api.get('/annuitydew/stats/playtime')
async def playtime(client: AsyncIOMotorClient = Depends(get_odm)):
    engine = AIOEngine(motor_client=client, database="backlogs")
    collection = engine.get_collection(BacklogGame)
    results = await collection.aggregate([{
        '$group': {
            '_id': None,
            'total_hours': {
                '$sum': '$game_hours'
            },
            'total_minutes': {
                '$sum': '$game_minutes'
            }
        }
    }]).to_list(length=None)
    # move chunks of 60 minutes into the hours count
    leftover_minutes = results[0].get('total_minutes') % 60
    hours_to_move = (results[0].get('total_minutes') - leftover_minutes) / 60
    results[0]['total_hours'] = int(results[0]['total_hours'] + hours_to_move)
    results[0]['total_minutes'] = int(leftover_minutes)

    return results[0]


@hysx_api.get('/annuitydew/search', response_model=List[BacklogGame])
async def search(client: AsyncIOMotorClient = Depends(get_odm), q: str = None):
    engine = AIOEngine(motor_client=client, database="backlogs")
    # change to plain q for OR results. f"\"{q}\"" is an AND search.
    if q == '':
        results = await engine.find(BacklogGame, sort=BacklogGame.id)
    else:
        results = await engine.find(
            BacklogGame,
            { '$text': { '$search': f"\"{q}\"" }},
            sort=BacklogGame.id,
        )

    return results


@hysx_api.get('/annuitydew/treemap')
async def system_treemap(backlog: List[BacklogGame] = Depends(get_all_games)):
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
    return json.loads(plotly.io.to_json(figure))


@hysx_api.get('/annuitydew/bubbles')
async def system_bubbles(backlog: List[BacklogGame] = Depends(get_all_games)):
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


@hysx_api.get('/annuitydew/timeline')
async def timeline(
    backlog: List[BacklogGame] = Depends(get_all_games),
    stats=Depends(count_by_status)
):
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
