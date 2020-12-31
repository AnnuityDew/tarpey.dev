# import native Python packages
from enum import Enum
from itertools import permutations
import json
from typing import List

# import third party packages
from fastapi import APIRouter, HTTPException, Depends, Path
import pandas
import plotly
import plotly.express as px
from pydantic import BaseModel, Field
import pymongo
from pymongo import MongoClient

# import custom local stuff
from api.db import get_dbm
from api.users import oauth2_scheme, UserOut


ml_api = APIRouter(
    prefix="/mildredleague",
    tags=["mildredleague"],
)


class Against(str, Enum):
    AGAINST = "against"
    FOR = "for"


class NickName(str, Enum):
    TARPEY = 'Tarpey'
    CHRISTIAN = 'Christian'
    NEEL = 'Neel'
    BRANDO = 'Brando'
    DEBBIE = 'Debbie'
    DANNY = 'Danny'
    MILDRED = 'Mildred'
    HARDY = 'Hardy'
    TOMMY = 'Tommy'
    BRYANT = 'Bryant'
    KINDY = 'Kindy'
    SENDZIK = 'Sendzik'
    SAMIK = 'Samik'
    STEPHANIE = 'Stephanie'
    DEBSKI = 'Debski'
    BEN = 'Ben'
    ARTHUR = 'Arthur'
    CONTI = 'Conti'
    FONTI = 'Fonti'
    FRANK = 'Frank'
    MIKE = 'mballen'
    PATRICK = 'Patrick'
    CHARLES = 'Charles'
    JAKE = 'Jake'
    BRAD = 'Brad'
    BYE = 'Bye'


class MLGame(BaseModel):
    doc_id: int = Field(..., alias='_id')
    away: str
    a_name: str
    a_nick: NickName
    a_division: str
    a_score: float
    home: str
    h_name: str
    h_nick: NickName
    h_division: str
    h_score: float
    week_s: int
    week_e: int
    season: int
    playoff: int


class MLTeam(BaseModel):
    doc_id: int = Field(..., alias='_id')
    team_name: str
    full_name: str
    nick_name: NickName
    season: int
    playoff_rank: int
    active: bool


class MLNote(BaseModel):
    doc_id: int = Field(..., alias='_id')
    season: int
    note: str


# couple of classes here that allow us to parameterize dependencies
class PlayoffChooser:
    def __init__(self, playoff: int):
        self.playoff = playoff
    
    def __call__(self, playoff: int):
        return self.playoff


regular_season = PlayoffChooser(0)
winners_playoff = PlayoffChooser(1)
losers_playoff = PlayoffChooser(2)


# declaring type of the client just helps with autocompletion.
@ml_api.get('/all/game/all', response_model=List[MLGame])
def get_all_games(client: MongoClient = Depends(get_dbm)):
    db = client.mildredleague
    collection = db.games
    # return full history of mildredleague games
    data = list(collection.find().sort("_id"))
    if not data:
        return "No data found!"
    else:
        return data


@ml_api.get('/all/game/{playoff}', response_model=List[MLGame])
def get_all_playoff_games(
    playoff: int = Path(..., title="Playoff flag.", description="0: regular, 1: playoffs, 2: losers", ge=0, le=2),
    client: MongoClient = Depends(get_dbm)
):
    db = client.mildredleague
    collection = db.games
    # return full history of mildredleague games
    data = list(collection.find({"playoff": playoff}).sort("_id"))
    if not data:
        return "No data found!"
    else:
        return data


@ml_api.get('/all/team/all')
def get_all_teams(client: MongoClient = Depends(get_dbm)):
    db = client.mildredleague
    collection = db.teams
    # return full history of mildredleague teams
    data = list(collection.find().sort("_id"))
    if not data:
        return "No data found!"
    else:
        return data


@ml_api.post('/game')
async def add_game(
    doc_list: List[MLGame],
    client: MongoClient = Depends(get_dbm),
    user: UserOut = Depends(oauth2_scheme),
):
    db = client.mildredleague
    collection = db.games
    try:
        collection.insert_many([doc.dict(by_alias=True) for doc in doc_list])
        # recalculate boxplot data for points for and against
        return doc_list
    except pymongo.errors.DuplicateKeyError:
        raise HTTPException(status_code=409, detail="Duplicate ID!")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f'Error! {e}')


@ml_api.get('/game/{doc_id}', response_model=MLGame)
async def get_game(
    doc_id: int,
    client: MongoClient = Depends(get_dbm),
):
    db = client.mildredleague
    collection = db.games
    doc = list(collection.find({'_id': doc_id}))
    if doc:
        return doc[0]
    else:
        return "No document found!"


@ml_api.put('/game')
async def edit_game(
    doc: MLGame,
    client: MongoClient = Depends(get_dbm),
    user: UserOut = Depends(oauth2_scheme),
):
    db = client.mildredleague
    collection = db.games
    collection.replace_one({'_id': doc.doc_id}, doc.dict(by_alias=True))
    # recalculate boxplot data, points for and against
    return "Success! Edited game " + str(doc.doc_id) + "."


@ml_api.delete('/game/{doc_id}')
async def delete_game(
    doc_id: int,
    client: MongoClient = Depends(get_dbm),
    user: UserOut = Depends(oauth2_scheme),
):
    db = client.mildredleague
    collection = db.games
    doc = collection.find_one_and_delete({'_id': doc_id})
    # recalculate boxplot data, points for and against
    if doc:
        return "Success! Deleted game " + str(doc_id) + "."
    else:
        return "Something weird happened..."


@ml_api.post('/note')
def add_note(
    doc: MLNote,
    client: MongoClient = Depends(get_dbm),
    user: UserOut = Depends(oauth2_scheme),
):
    db = client.mildredleague
    collection = db.notes
    try:
        collection.insert_one(doc.dict(by_alias=True))
        return "Success! Added note " + str(doc.doc_id) + "."
    except pymongo.errors.DuplicateKeyError:
        return "Note " + str(doc.doc_id) + " already exists!"


@ml_api.get('/note/{doc_id}', response_model=MLNote)
def get_note(doc_id: int, client: MongoClient = Depends(get_dbm)):
    db = client.mildredleague
    collection = db.notes
    doc = list(collection.find({'_id': doc_id}))
    if doc:
        return doc[0]
    else:
        return "No document found!"


@ml_api.put('/note')
def edit_note(
    doc: MLNote,
    client: MongoClient = Depends(get_dbm),
    user: UserOut = Depends(oauth2_scheme),
):
    db = client.mildredleague
    collection = db.notes
    collection.replace_one({'_id': doc.doc_id}, doc.dict(by_alias=True))
    return "Success! Edited note " + str(doc.doc_id) + "."


@ml_api.delete('/note/{doc_id}')
def delete_note(
    doc_id: int,
    client: MongoClient = Depends(get_dbm),
    user: UserOut = Depends(oauth2_scheme),
):
    db = client.mildredleague
    collection = db.notes
    doc = collection.find_one_and_delete({'_id': doc_id})
    if doc:
        return "Success! Deleted game " + str(doc_id) + "."
    else:
        return "Something weird happened..."



@ml_api.get('/all-time-ranking-fig')
def all_time_ranking_fig(teams_data: List[MLTeam] = Depends(get_all_teams)):
    # convert to pandas dataframe
    ranking_df = pandas.DataFrame(teams_data)
    # pivot by year for all teams
    annual_ranking_df = pandas.pivot(
        ranking_df,
        index='nick_name',
        columns='season',
        values='playoff_rank'
    )

    # temporary variable to rank relevance of a team.
    # higher numbers are less relevant.
    # 15 for teams that didn't play in a given year
    # (worst rank for a team that existed would be 14)
    annual_ranking_df_temp = annual_ranking_df.fillna(15)
    annual_ranking_df_temp['relevance'] = annual_ranking_df_temp.sum(axis=1)
    annual_ranking_df['relevance'] = annual_ranking_df_temp['relevance']
    annual_ranking_df.sort_values(by='relevance', ascending=False, inplace=True)
    annual_ranking_df.reset_index(inplace=True)

    # y axis labels
    y_ranking_names = annual_ranking_df.nick_name.to_list()

    # drop unnecessary columns
    annual_ranking_df.drop(columns=['nick_name', 'relevance'], inplace=True)

    # x axis labels
    x_seasons = annual_ranking_df.columns.tolist()

    # need to pull out of data frame format for this particular figure,
    # and replace np.nan with 0 (to then replace with None)
    z_rankings = annual_ranking_df.fillna(0).values.tolist()

    heatmap_colors = [
        [i / (len(plotly.colors.diverging.Temps) - 1), color]
        for i, color in enumerate(plotly.colors.diverging.Temps)
    ]

    return {
        'x_seasons': x_seasons,
        'y_ranking_names': y_ranking_names,
        'z_rankings': z_rankings,
        'heatmap_colors': heatmap_colors,
    }


@ml_api.get('/win-total-fig')
def win_total_fig(playoff: bool = False, games_data: List[MLGame] = Depends(get_all_games)):
    # convert to pandas DataFrame and normalize
    games_df = pandas.DataFrame(games_data)
    games_df = normalize_games(games_df)
    # regular season df or playoff df?
    if playoff is False:
        games_df = games_df.loc[games_df.playoff == 0]
    else:
        games_df = games_df.loc[games_df.playoff == 1]
    # convert to record_df
    record_df = calc_records(
        games_df
    )
    # group by nick_name (don't need division info for this figure)
    record_df = record_df.groupby(
        level=['nick_name'],
    ).agg(
        {'win_total': sum}
    ).sort_values('win_total', ascending=True)

    # create list of x_data and y_data
    x_data = [int(data_point) for data_point in list(record_df.win_total.values)]
    y_data = record_df.index.tolist()
    # color data needs to be tripled to have enough
    # colors for every bar!
    color_data = (
        px.colors.cyclical.Phase[1:] +
        px.colors.cyclical.Phase[1:] +
        px.colors.cyclical.Phase[1:]
    )

    return {
        'x_data': x_data,
        'y_data': y_data,
        'color_data': color_data,
    }


@ml_api.get('/heatmap-fig')
def matchup_heatmap_fig(
    games_data: List[MLGame] = Depends(get_all_games),
    teams_data: List[MLTeam] = Depends(get_all_teams),
):
    # convert to pandas DataFrame
    games_df = pandas.DataFrame(games_data)
    # normalize games
    games_df = normalize_games(games_df)
    # convert to record_df
    matchup_df = calc_matchup_records(
        games_df
    ).reset_index()
    # pull all-time file to filter active teams
    ranking_df = pandas.DataFrame(teams_data)

    # inner joins are just to keep active teams
    active_matchup_df = matchup_df.merge(
        ranking_df.loc[
            ranking_df.active == 'yes',
            ['nick_name']
        ].drop_duplicates(),
        on='nick_name',
        how='inner',
    ).merge(
        ranking_df.loc[
            ranking_df.active == 'yes',
            ['nick_name']
        ].drop_duplicates(),
        left_on='loser',
        right_on='nick_name',
        how='inner',
    ).drop(
        columns=['nick_name_y']
    ).rename(
        columns={'nick_name_x': 'nick_name'}
    ).set_index(keys=['nick_name', 'loser'])

    # game total custom data for the hover text
    game_df = active_matchup_df[['game_total']].unstack()
    # win pct data is what drives the figure
    matchup_df = active_matchup_df[['win_pct']].unstack()

    # start creating the figure!
    # y axis labels
    y_winners = matchup_df.index.to_list()
    y_winners.reverse()
    # x axis labels
    x_opponents = matchup_df.columns.get_level_values(1).to_list()
    # z axis data, replacing nan with 0s
    z_matchup_data = matchup_df[['win_pct']].fillna(-1).values.tolist()
    z_matchup_data.reverse()
    # custom hovertext data, replacing nan with 0s
    hover_data = game_df[['game_total']].fillna(0).values.tolist()
    hover_data.reverse()
    # color data
    matchup_colors = [
        [i / (len(plotly.colors.diverging.Temps_r) - 1), color]
        for i, color in enumerate(plotly.colors.diverging.Temps_r)
    ]

    return {
        'x_opponents': x_opponents,
        'y_winners': y_winners,
        'z_matchup_data': z_matchup_data,
        'matchup_colors': matchup_colors,
        'hover_data': hover_data
    }


@ml_api.get('/{season}/game/all', response_model=List[MLGame])
def get_season_games(season: int, client: MongoClient = Depends(get_dbm)):
    db = client.mildredleague
    collection = db.games
    # return all results if no search_term
    data = list(collection.find({"season": season}).sort("_id"))
    if not data:
        return "No data found!"
    else:
        return data


@ml_api.get('/{season}/game/{playoff}', response_model=List[MLGame])
def get_season_games_subset(
    season: int,
    playoff: int = Path(..., title="Playoff flag.", description="0: regular, 1: playoffs, 2: losers", ge=0, le=2),
    client: MongoClient = Depends(get_dbm),
):
    db = client.mildredleague
    collection = db.games
    # return all results if no search_term
    data = list(collection.find({"season": season, "playoff": playoff}).sort("_id"))
    if not data:
        return "No data found!"
    else:
        return data


@ml_api.get('/{season}/note/all', response_model=List[MLNote])
def get_season_notes(season: int, client: MongoClient = Depends(get_dbm)):
    db = client.mildredleague
    collection = db.notes
    # return all results if no search_term
    doc_list = list(collection.find({"season": season}).sort("_id"))
    if doc_list:
        return doc_list
    else:
        return "No documents found!"


@ml_api.get('/{season}/boxplot')
def season_boxplot_fig(
    season: int,
    client: MongoClient = Depends(get_dbm),
    games_data: List[MLGame] = Depends(get_season_games),
    teams_data: List[MLTeam] = Depends(get_all_teams)
):
    '''Ideally something like this would go back to being cached, but
    we still need to figure that out wtih FastAPI!

    '''
    # convert to DataFrame
    season_df = pandas.DataFrame(games_data)
    # normalized score columns for two-week playoff games
    season_df['a_score_norm'] = (
        season_df['a_score'] / (
            season_df['week_e'] - season_df['week_s'] + 1
        )
    )
    season_df['h_score_norm'] = (
        season_df['h_score'] / (
            season_df['week_e'] - season_df['week_s'] + 1
        )
    )
    # we just want unique scores. so let's stack away and home.
    # this code runs to analyze Points For.
    score_df_for = season_df[['a_nick', 'a_score_norm']].rename(
        columns={'a_nick': 'name', 'a_score_norm': 'score'},
    ).append(
        season_df[['h_nick', 'h_score_norm']].rename(
            columns={'h_nick': 'name', 'h_score_norm': 'score'},
        ),
        ignore_index=True,
    )
    score_df_for['side'] = 'for'
    # this code runs to analyze Points Against.
    score_df_against = season_df[['a_nick', 'h_score_norm']].rename(
        columns={'a_nick': 'name', 'h_score_norm': 'score'},
    ).append(
        season_df[['h_nick', 'a_score_norm']].rename(
            columns={'h_nick': 'name', 'a_score_norm': 'score'},
        ),
        ignore_index=True,
    )
    score_df_against['side'] = 'against'
    score_df = pandas.concat([score_df_for, score_df_against])
    # let's sort by playoff rank instead
    # read season file, but we only need nick_name, season, and playoff_rank
    ranking_df = pandas.DataFrame(teams_data)[['nick_name', 'season', 'playoff_rank']]
    # merge this (filtered by season) into score_df so we can sort values
    score_df = score_df.merge(
        ranking_df.loc[ranking_df.season == int(season), ['nick_name', 'playoff_rank']],
        left_on=['name'],
        right_on=['nick_name'],
        how='left',
    ).sort_values(
        by='playoff_rank', ascending=True,
    )

    # add a unique _id for Mongo
    score_df['_id'] = range(1, len(score_df) + 1)

    # convert back to json for writing to Mongo
    doc_list = json.loads(score_df.to_json(orient='records'))

    # write data to MongoDB
    db = client.mildredleague
    collection = getattr(db, 'boxplot' + str(season))
    if list(collection.find().sort("_id")) == doc_list:
        message = str(season) + " boxplot chart is already synced!"
    else:
        # if boxplots need to be recalculated, just wipe the collection and reinsert
        collection.delete_many({})
        collection.insert_many(doc_list)
        message = "Bulk delete and insert complete!"

    data = list(collection.find({"name": {'$ne': 'Bye'}}).sort("_id"))

    # convert to pandas DataFrame
    score_df = pandas.DataFrame(data)

    # for and against split
    score_df_for = score_df.loc[score_df.side == 'for']
    score_df_against = score_df.loc[score_df.side == 'against']

    # names on the X axis
    x_data_for = score_df_for.nick_name.unique().tolist()
    x_data_against = score_df_against.nick_name.unique().tolist()

    # Y axis is scores. need 2D array
    y_data_for = [
        score_df_for.loc[
            score_df_for.nick_name == name, 'score'
        ].tolist() for name in x_data_for
    ]
    y_data_against = [
        score_df_against.loc[
            score_df_against.nick_name == name, 'score'
        ].tolist() for name in x_data_against
    ]

    # list of hex color codes
    color_data = px.colors.qualitative.Light24

    return {
        'message': message,
        'for_data': {
            'x_data': x_data_for,
            'y_data': y_data_for,
            'color_data': color_data,
        },
        'against_data': {
            'x_data': x_data_against,
            'y_data': y_data_against,
            'color_data': color_data,
        },
    }


@ml_api.get('/{season}/table')
def season_table(
    season: int,
    games_data: List[MLGame] = Depends(get_season_games_subset),
    teams_data: List[MLTeam] = Depends(get_all_teams),
):
    '''Only use the else statement for the active season, to
    resolve tiebreakers.'''
    games_df = pandas.DataFrame(games_data)
    games_df = normalize_games(games_df)
    if season < 2020:
        # run calc records for the season
        season_records_df = calc_records(
            games_df
        )
        # pull all rankings and filter for the season
        season_ranking_df = pandas.DataFrame(teams_data).set_index('_id')
        season_ranking_df = season_ranking_df.loc[season_ranking_df.season == int(season)]
        # merge playoff ranking and active status
        season_table = season_records_df.merge(
            season_ranking_df[['nick_name', 'playoff_rank', 'active']],
            on='nick_name',
            how='left',
        ).sort_values(
            by=['playoff_rank', 'loss_total'], ascending=True
        )
        return json.loads(season_table.to_json(orient='table', index=False))
    else:
        # to resolve tiebreakers, need records for the season
        season_records_df = calc_records(
            games_df
        )
        # also bring in H2H matchup records
        matchup_df = calc_matchup_records(
            games_df
        )

        # initial division ranking before tiebreakers.
        season_records_df['division_rank'] = season_records_df.groupby(
            level=['division'],
        )['win_pct'].rank(
            method='min',
            ascending=False,
        )

        # begin loop to resolve division ties.
        for div in season_records_df.index.unique(level='division'):
            # filter down to the division of interest.
            div_df = season_records_df.loc[[div]]
            # let's calculate division record here
            div_matchups = list(permutations(div_df.index.get_level_values('nick_name'), 2))
            # group by winner to determine H2H among the group
            div_matchup_df = matchup_df.loc[div_matchups].groupby(
                level='nick_name'
            ).agg(
                {'win_total': sum, 'game_total': sum}
            )
            # win_pct in the divisional grouping, then join back to div_df
            div_matchup_df['win_pct_div'] = (
                div_matchup_df['win_total'] / div_matchup_df['game_total']
            )
            div_df = div_df.join(div_matchup_df[['win_pct_div']])
            # loop over division_rank to determine where ties need to be broken.
            for rank in div_df.division_rank.unique():
                # if the length of the df is longer than 1 for any rank, there's a tie...
                tied_df = div_df.loc[div_df.division_rank == rank]
                if len(tied_df) > 1:
                    untied_df = division_tiebreaker_one(tied_df, games_df, matchup_df)
                    div_df.update(untied_df)
            season_records_df.update(div_df)

        # begin to determine playoff seed. first, separate the three division winners.
        div_winners_df = season_records_df.loc[season_records_df.division_rank == 1]
        div_losers_df = season_records_df.loc[season_records_df.division_rank > 1]
        # calculate initial seeding based on pure win_pct.
        div_winners_df['playoff_seed'] = div_winners_df.win_pct.rank(
            method='min',
            ascending=False,
        )
        div_losers_df['playoff_seed'] = div_losers_df.win_pct.rank(
            method='min',
            ascending=False,
        ) + len(div_winners_df)

        # now, tiebreakers...winners first
        for seed in range(1, len(div_winners_df)):
            # if the length of the df is longer than 1 for any rank, there's a tie...
            tied_df = div_winners_df.loc[div_winners_df.playoff_seed == seed]
            if len(tied_df) > 1:
                untied_df = wild_card_tiebreaker_one(tied_df, games_df, matchup_df)
                div_winners_df.update(untied_df)

        # break the rest of the ties for division losers.
        for seed in range(len(div_winners_df) + 1, len(season_records_df)):
            # if the length of the df is longer than 1 for any rank, there's a tie...
            tied_df = div_losers_df.loc[div_losers_df.playoff_seed == seed]
            if len(tied_df) > 1:
                untied_df = wild_card_tiebreaker_one(tied_df, games_df, matchup_df)
                div_losers_df.update(untied_df)

        season_table = pandas.concat(
            [div_winners_df, div_losers_df]
        ).sort_values(
            by='playoff_seed'
        )

        return json.loads(season_table.reset_index().to_json(orient='table', index=False))


@ml_api.get("/{season}/sim")
def seed_sim(
    season: int,
    games_data: List[MLGame] = Depends(get_season_games),
    winners_array=['t1', 't2', 't3', 't4', 't5', 't6', 't7'],
):
    # this function will need to be reimplemented next year!
    # return garbage for now.
    return winners_array
    # convert to dataframe
    games_df = pandas.DataFrame(games_data).set_index('_id')

    # we're going to concatenate the API data with simulated data
    # that the user has chosen, so we can rerun tiebreakers
    sim_df = pandas.DataFrame(
        data=[
            [
                'Division 6',
                'Referees',
                'AFC East',
                'Division 6',
                'Referees',
                'AFC East',
                'Referees',
            ],
            ['sim' for i in range(0, 7)],
            [
                'Tarpey',
                'Charles',
                'Conti',
                'Frank',
                'mballen',
                'Jake',
                'Brad',
            ],
            [
                winners_array.count('Tarpey')*20 + 80,
                winners_array.count('Charles')*20 + 80,
                winners_array.count('Conti')*20 + 80,
                winners_array.count('Frank')*20 + 80,
                winners_array.count('mballen')*20 + 80,
                winners_array.count('Jake')*20 + 80,
                winners_array.count('Brad')*20 + 80,
            ],
            ['sim' for i in range(0, 7)],
            [
                'Division 6',
                'Referees',
                'AFC East',
                'Division 6',
                'AFC East',
                'AFC East',
                'Referees',
            ],
            ['sim' for i in range(0, 7)],
            [
                'Brando',
                'Mildred',
                'Samik',
                'Fonti',
                'Sendzik',
                'Kindy',
                'Tommy',
            ],
            [
                winners_array.count('Brando')*20 + 80,
                winners_array.count('Mildred')*20 + 80,
                winners_array.count('Samik')*20 + 80,
                winners_array.count('Fonti')*20 + 80,
                winners_array.count('Sendzik')*20 + 80,
                winners_array.count('Kindy')*20 + 80,
                winners_array.count('Tommy')*20 + 80,
            ],
            ['sim' for i in range(0, 7)],
            [0 for i in range(0, 7)],
            [2020 for i in range(0, 7)],
            [14 for i in range(0, 7)],
            [14 for i in range(0, 7)],
        ]
    ).transpose()
    sim_df.columns = games_df.columns.tolist()
    sim_df = pandas.concat([games_df, sim_df], ignore_index=True)

    # table = season_table_active(season, sim_df)[[
    #     'division',
    #     'nick_name',
    #     'win_total',
    #     'loss_total',
    #     'tie_total',
    #     'division_rank',
    #     'playoff_seed',
    # ]]

    return None


def normalize_games(all_games_df):
    # which team won?
    all_games_df['a_win'] = 0
    all_games_df['h_win'] = 0
    all_games_df['a_tie'] = 0
    all_games_df['h_tie'] = 0
    # away win
    all_games_df.loc[all_games_df.a_score > all_games_df.h_score, 'a_win'] = 1
    # home win
    all_games_df.loc[all_games_df.a_score < all_games_df.h_score, 'h_win'] = 1
    # tie
    all_games_df.loc[all_games_df.a_score == all_games_df.h_score, ['a_tie', 'h_tie']] = 1
    # normalized score columns for two-week playoff games
    all_games_df['a_score_norm'] = (
        all_games_df['a_score'] / (
            all_games_df['week_e'] - all_games_df['week_s'] + 1
        )
    )
    all_games_df['h_score_norm'] = (
        all_games_df['h_score'] / (
            all_games_df['week_e'] - all_games_df['week_s'] + 1
        )
    )
    # margin = home - away
    all_games_df['h_margin'] = all_games_df['h_score_norm'] - all_games_df['a_score_norm']

    return all_games_df


def calc_records(games_df):
    # season wins/losses/ties/PF/PA for away teams, home teams
    away_df = pandas.pivot_table(
        games_df.convert_dtypes(),
        values=['a_win', 'h_win', 'a_tie', 'a_score_norm', 'h_score_norm'],
        index=['a_division', 'a_nick'],
        aggfunc='sum',
        fill_value=0
        )
    home_df = pandas.pivot_table(
        games_df.convert_dtypes(),
        values=['h_win', 'a_win', 'h_tie', 'h_score_norm', 'a_score_norm'],
        index=['h_division', 'h_nick'],
        aggfunc='sum',
        fill_value=0
        )

    # rename index and against columns
    away_df = away_df.rename(
        columns={'h_win': 'a_loss', 'h_score_norm': 'a_score_norm_against'},
    ).rename_axis(
        index={'a_nick': 'nick_name', 'a_division': 'division'}
    )
    home_df = home_df.rename(
        columns={'a_win': 'h_loss', 'a_score_norm': 'h_score_norm_against'},
    ).rename_axis(
        index={'h_nick': 'nick_name', 'h_division': 'division'}
    )
    # merge to one table
    record_df = home_df.join(
        away_df,
        how='inner',
        )
    # win total, loss total, game total, points for, points against, win percentage
    record_df['win_total'] = record_df['h_win'] + record_df['a_win']
    record_df['loss_total'] = record_df['h_loss'] + record_df['a_loss']
    record_df['tie_total'] = record_df['h_tie'] + record_df['a_tie']
    record_df['games_played'] = record_df['win_total'] + record_df['loss_total'] + record_df['tie_total']
    record_df['win_pct'] = (record_df['win_total'] + record_df['tie_total'] * 0.5) / record_df['games_played']
    record_df['points_for'] = record_df['h_score_norm'] + record_df['a_score_norm']
    record_df['points_against'] = record_df['h_score_norm_against'] + record_df['a_score_norm_against']
    record_df['avg_margin'] = (record_df['points_for'] - record_df['points_against']) / record_df['games_played']
    record_df.sort_values(by='win_pct', ascending=False, inplace=True)
    record_df.drop(
        columns=[
            'h_win',
            'a_win',
            'h_loss',
            'a_loss',
            'h_tie',
            'a_tie',
            'h_score_norm',
            'a_score_norm',
            'h_score_norm_against',
            'a_score_norm_against',
        ],
        inplace=True,
    )

    return record_df


def calc_matchup_records(games_df):
    # grouping for away and home matchup winners, ties, occurrences
    away_df = pandas.pivot_table(
        games_df,
        values=['a_win', 'a_tie', 'season'],
        index=['a_nick', 'h_nick'],
        aggfunc={
            'a_win': 'sum',
            'a_tie': 'sum',
            'season': 'count',
        },
        fill_value=0,
        ).rename(columns={'season': 'a_games'})
    home_df = pandas.pivot_table(
        games_df,
        values=['h_win', 'h_tie', 'season'],
        index=['h_nick', 'a_nick'],
        aggfunc={
            'h_win': 'sum',
            'h_tie': 'sum',
            'season': 'count',
        },
        fill_value=0,
        ).rename(columns={'season': 'h_games'})
    # rename indices
    away_df.index.set_names(names=['nick_name', 'loser'], inplace=True)
    home_df.index.set_names(names=['nick_name', 'loser'], inplace=True)
    # join and sum to get total matchup wins
    matchup_df = away_df.join(
        home_df,
        how='outer',
    ).fillna(0).convert_dtypes()
    # ties count for 0.5
    matchup_df['win_total'] = (
        matchup_df['a_win'] +
        matchup_df['h_win'] +
        matchup_df['a_tie'] * 0.5 +
        matchup_df['h_tie'] * 0.5
    )
    matchup_df['game_total'] = (
        matchup_df['a_games'] +
        matchup_df['h_games']
    )
    # get rid of intermediate columns. just wins and games now
    matchup_df = matchup_df.convert_dtypes().drop(
        columns=[
            'a_win',
            'h_win',
            'a_tie',
            'h_tie',
            'a_games',
            'h_games',
        ]
    )
    # add win pct column and sort by
    matchup_df['win_pct'] = matchup_df['win_total'] / matchup_df['game_total']
    matchup_df.sort_values(by=['win_pct'], ascending=False, inplace=True)

    return matchup_df


def division_tiebreaker_one(tied_df, games_df, matchup_df):
    # figure out who's got H2H among the 2+ teams by generating all possible matchups
    matchups = list(permutations(tied_df.index.get_level_values('nick_name'), 2))
    # group by winner to determine H2H among the group
    matchup_df = matchup_df.loc[matchups].groupby(
        level='nick_name'
    ).agg(
        {'win_total': sum, 'game_total': sum}
    )
    # win_pct in this H2H grouping
    matchup_df['win_pct_h2h'] = matchup_df['win_total'] / matchup_df['game_total']
    matchup_df['tiebreaker_rank'] = matchup_df.win_pct_h2h.rank(
        method='min',
        ascending=False,
    ) - 1

    # recalculate div rank now
    tied_df = tied_df.join(matchup_df[['tiebreaker_rank']])
    tied_df['division_rank'] = tied_df['division_rank'] + tied_df['tiebreaker_rank']

    # check time! are we still tied or is it broken?
    for rank in tied_df.division_rank.unique():
        # if the length of the df is longer than 1 for any rank, there's a tie...
        # proceed to tiebreaker #2, which is division record.
        still_tied_df = tied_df.loc[tied_df.division_rank == rank]
        if len(still_tied_df) > 1:
            untied_df = division_tiebreaker_two(still_tied_df)
            tied_df.update(untied_df)

    return tied_df


def division_tiebreaker_two(tied_df):
    # rank based on win_pct_div
    tied_df['tiebreaker_two_rank'] = tied_df.win_pct_div.rank(
        method='min',
        ascending=False,
    ) - 1

    # recalculate div rank now
    tied_df['division_rank'] = tied_df['division_rank'] + tied_df['tiebreaker_two_rank']

    # check time! are we still tied or is it broken?
    for rank in tied_df.division_rank.unique():
        # if the length of the df is longer than 1 for any rank, there's a tie...
        # proceed to tiebreaker #3, which is points for.
        still_tied_df = tied_df.loc[tied_df.division_rank == rank]
        if len(still_tied_df) > 1:
            untied_df = division_tiebreaker_three(still_tied_df)
            tied_df.update(untied_df)

    return tied_df


def division_tiebreaker_three(tied_df):
    # rank based on points for
    tied_df['tiebreaker_three_rank'] = tied_df.points_for.rank(
        method='min',
        ascending=False,
    ) - 1

    # recalculate div rank now
    tied_df['division_rank'] = tied_df['division_rank'] + tied_df['tiebreaker_three_rank']

    # check time! are we still tied or is it broken?
    for rank in tied_df.division_rank.unique():
        # if the length of the df is longer than 1 for any rank, there's a tie...
        # proceed to tiebreaker #4, which is points against
        still_tied_df = tied_df.loc[tied_df.division_rank == rank]
        if len(still_tied_df) > 1:
            untied_df = division_tiebreaker_four(still_tied_df)
            tied_df.update(untied_df)

    return tied_df


def division_tiebreaker_four(tied_df):
    # rank based on points against
    tied_df['tiebreaker_four_rank'] = tied_df.points_against.rank(
        method='min',
        ascending=False,
    ) - 1

    # recalculate div rank now
    tied_df['division_rank'] = tied_df['division_rank'] + tied_df['tiebreaker_four_rank']

    # check time! are we still tied or is it broken?
    for rank in tied_df.division_rank.unique():
        # if the length of the df is longer than 1 for any rank, there's a tie...
        # proceed to tiebreaker #5, which is a real life coin flip.
        still_tied_df = tied_df.loc[tied_df.division_rank == rank]
        if len(still_tied_df) > 1:
            print(still_tied_df)
            print("You're gonna need a coin for this one.")

    return tied_df


def wild_card_tiebreaker_one(tied_df, games_df, matchup_df):
    # need to filter out any teams at this stage that aren't the highest-ranked
    # team in their division in the tiebreaker.
    seed_to_break = tied_df.playoff_seed.min()
    # if this tiebreaker only involves one division, just use division ranking
    if len(tied_df.index.unique(level='division')) == 1:
        tied_df['playoff_seed'] = tied_df.division_rank.rank(
            method='min',
            ascending=True,
        ) + seed_to_break - 1
    else:
        # with two or more divisions involved, it's on to H2H record.
        # but we can only compare the top remaining team in each division.
        # here we need to filter any team that doesn't meet that criteria
        # and add one to their playoff seed, so they'll be included
        # in the next tiebreaker sequence.
        # let's do a groupby object to get the min division rank in each
        # division.
        filter_df = tied_df.groupby(
            'division'
            ).agg(
                {'division_rank': min}
            ).rename(
                columns={'division_rank': 'qualifying_rank'}
            )
        # if we're looping back through here after a qualifying rank was
        # determined in an earlier tiebreak for the same seed, this join will blow up
        # (we don't need to recalculate the qualifying rank until looking
        # at the next seed). so check for qualifying rank here before joining
        if 'qualifying_rank' not in tied_df.columns:
            tied_df = tied_df.join(filter_df)
        # split the tied_df here between teams that qualify to continue
        # the tiebreaker and teams that have to wait for the next seed
        qualified_tied_df = tied_df.loc[tied_df.division_rank == tied_df.qualifying_rank]
        disqualified_tied_df = tied_df.loc[tied_df.division_rank != tied_df.qualifying_rank]

        # send qualified teams to the next tiebreaker. when they return, concat
        # with the disqualified teams
        untied_df = wild_card_tiebreaker_two(qualified_tied_df, games_df, matchup_df, seed_to_break)

        # for wild card seeds, only one team can advance at a time.
        # the rest of the remaining teams have to be reconsidered in the next
        # seed's tiebreaker, so we reset seeds that weren't really tiebroken here.
        disqualified_tied_df['playoff_seed'] = seed_to_break + 1

        # concat happens here inside the update
        tied_df.update(pandas.concat([untied_df, disqualified_tied_df]))

    return tied_df


def wild_card_tiebreaker_two(tied_df, games_df, matchup_df, seed_to_break):
    # figure out who's got H2H among the 2-3 teams by generating all possible matchups
    matchups = list(permutations(tied_df.index.get_level_values('nick_name'), 2))
    # group by winner to determine H2H among the group
    wc_matchup_df = matchup_df.loc[matchup_df.index.intersection(matchups)].groupby(
        level='nick_name'
    ).agg(
        {'win_total': sum, 'game_total': sum}
    )
    # win_pct in this H2H grouping
    wc_matchup_df['win_pct_h2h'] = wc_matchup_df['win_total'] / wc_matchup_df['game_total']

    # our sweep check will just be whether or not game_total in a row is
    # 1 (in case of a 2-way tie) or 2 (in case of a 3-way tie). If it's not,
    # H2H will be skipped for that team (set win_pct_h2h to .500)
    wc_matchup_df.loc[
        wc_matchup_df.game_total < len(wc_matchup_df) - 1,
        'win_pct_h2h'] = 0.5

    # now determine H2H rank in the group
    wc_matchup_df['wc_tiebreaker_two_rank'] = wc_matchup_df.win_pct_h2h.rank(
        method='min',
        ascending=False,
    ) - 1

    # if we're looping back through here after a tiebreaker rank was
    # determined in an earlier tiebreak for the same seed, this join will blow up
    # so check for tiebreaker rank here before joining. if the column
    # is already there, just update it.
    if 'wc_tiebreaker_two_rank' not in tied_df.columns:
        tied_df = tied_df.join(wc_matchup_df[['wc_tiebreaker_two_rank']])
    else:
        tied_df.update(wc_matchup_df[['wc_tiebreaker_two_rank']])

    # if this is a two way tiebreaker where there was no H2H,
    # we'll have to fill in tiebreaker_two with zeroes
    # before we modify the playoff seed
    tied_df['wc_tiebreaker_two_rank'] = tied_df['wc_tiebreaker_two_rank'].fillna(0)

    # now modify playoff seed
    tied_df['playoff_seed'] = tied_df['playoff_seed'] + tied_df['wc_tiebreaker_two_rank']

    # for wild card seeds, only one team can advance at a time.
    # the rest of the remaining teams have to be reconsidered in the next
    # seed's tiebreaker, so we reset seeds that weren't really tiebroken here.
    tied_df.loc[tied_df.playoff_seed != seed_to_break, 'playoff_seed'] = seed_to_break + 1

    # check time! are we still tied or is it broken?
    # if the count of teams at the seed_to_break is the same as before,
    # proceed to tiebreaker #3, which is points for.
    still_tied_df = tied_df.loc[tied_df.playoff_seed == seed_to_break]
    disqualified_tied_df = tied_df.loc[tied_df.playoff_seed > seed_to_break]
    if len(still_tied_df) == len(tied_df):
        untied_df = wild_card_tiebreaker_three(still_tied_df, seed_to_break)
        tied_df.update(untied_df)
    # there's also the case where someone has dropped out of the tiebreaker;
    # here we need to restart from step one with just the remaining teams.
    elif len(still_tied_df) > 1:
        untied_df = wild_card_tiebreaker_one(still_tied_df, games_df, matchup_df)
        tied_df.update(pandas.concat([untied_df, disqualified_tied_df]))

    return tied_df


def wild_card_tiebreaker_three(tied_df, seed_to_break):
    # rank based on points for
    tied_df['wc_tiebreaker_three_rank'] = tied_df.points_for.rank(
        method='min',
        ascending=False,
    ) - 1

    # recalculate playoff seed now
    tied_df['playoff_seed'] = tied_df['playoff_seed'] + tied_df['wc_tiebreaker_three_rank']

    # for wild card seeds, only one team can advance at a time.
    # the rest of the remaining teams have to be reconsidered in the next
    # seed's tiebreaker, so we reset seeds that weren't really tiebroken here.
    tied_df.loc[tied_df.playoff_seed != seed_to_break, 'playoff_seed'] = seed_to_break + 1

    # check time! are we still tied or is it broken?
    # if the count of teams at the seed_to_break is the same as before,
    # proceed to tiebreaker #4, which is points against.
    still_tied_df = tied_df.loc[tied_df.playoff_seed == seed_to_break]
    disqualified_tied_df = tied_df.loc[tied_df.playoff_seed > seed_to_break]
    if len(still_tied_df) == len(tied_df):
        untied_df = wild_card_tiebreaker_four(still_tied_df, seed_to_break)
        tied_df.update(untied_df)
    # there's also the case where someone has dropped out of the tiebreaker;
    # here we need to restart from step one with just the remaining teams.
    elif len(still_tied_df) > 1:
        untied_df = wild_card_tiebreaker_one(still_tied_df)
        tied_df.update(pandas.concat([untied_df, disqualified_tied_df]))

    return tied_df


def wild_card_tiebreaker_four(tied_df, seed_to_break):
    # rank based on points against
    tied_df['wc_tiebreaker_four_rank'] = tied_df.points_against.rank(
        method='min',
        ascending=False,
    ) - 1

    # recalculate playoff seed now
    tied_df['playoff_seed'] = tied_df['playoff_seed'] + tied_df['wc_tiebreaker_four_rank']

    # for wild card seeds, only one team can advance at a time.
    # the rest of the remaining teams have to be reconsidered in the next
    # seed's tiebreaker, so we reset seeds that weren't really tiebroken here.
    tied_df.loc[tied_df.playoff_seed != seed_to_break, 'playoff_seed'] = seed_to_break + 1

    # check time! are we still tied or is it broken?
    # if the count of teams at the seed_to_break is the same as before,
    # proceed to tiebreaker #5, which is an irl coin flip.
    still_tied_df = tied_df.loc[tied_df.playoff_seed == seed_to_break]
    disqualified_tied_df = tied_df.loc[tied_df.playoff_seed > seed_to_break]
    if len(still_tied_df) == len(tied_df):
        print(still_tied_df)
        print("You're gonna need a coin for this one. Or maybe a six-sided die.")
    # there's also the case where someone has dropped out of the tiebreaker;
    # here we need to restart from step one with just the remaining teams.
    elif len(still_tied_df) > 1:
        untied_df = wild_card_tiebreaker_one(still_tied_df)
        tied_df.update(pandas.concat([untied_df, disqualified_tied_df]))

    return tied_df
