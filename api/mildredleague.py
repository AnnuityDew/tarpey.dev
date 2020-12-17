# import native Python packages
from enum import Enum
import json
from typing import List

# import third party packages
from fastapi import APIRouter, Depends
import pandas
from pydantic import BaseModel, Field
import pymongo
from pymongo import MongoClient

# import custom local stuff
from api.db import get_dbm


ml_api = APIRouter(
    prefix="/mildredleague",
    tags=["mildredleague"],
)


class MLGame(BaseModel):
    doc_id: int = Field(..., alias='_id')
    away: str
    a_name: str
    a_nick: str
    a_division: str
    a_score: float
    home: str
    h_name: str
    h_nick: str
    h_division: str
    h_score: float
    week_s: int
    week_e: int
    season: int
    playoff: int


class MLNote(BaseModel):
    doc_id: int = Field(..., alias='_id')
    season: int
    note: str


class Against(str, Enum):
    AGAINST = "against"
    FOR = "for"


# declaring type of the client just helps with autocompletion.
@ml_api.post('/add-game')
def add_game(doc: MLGame, client: MongoClient = Depends(get_dbm)):
    db = client.mildredleague
    collection = db.games
    try:
        collection.insert_one(doc.dict(by_alias=True))
        # recalculate boxplot data for points for and against
        for boxplot in ['for', 'against']:
            season_boxplot_transform(
                season=doc.season,
                against=boxplot,
            )
        return "Success! Added game " + str(doc.doc_id) + "."
    except pymongo.errors.DuplicateKeyError:
        return "Game " + str(doc.doc_id) + " already exists!"


@ml_api.get('/get-game/{doc_id}', response_model=MLGame)
async def get_game(doc_id: int, client: MongoClient = Depends(get_dbm)):
    db = client.mildredleague
    collection = db.games
    doc = list(collection.find({'_id': doc_id}))
    if doc:
        return doc[0]
    else:
        return "No document found!"


@ml_api.put('/edit-game')
def edit_game(doc: MLGame, client: MongoClient = Depends(get_dbm)):
    db = client.mildredleague
    collection = db.games
    collection.replace_one({'_id': doc.doc_id}, doc)
    # recalculate boxplot data, points for and against
    for boxplot in ['for', 'against']:
        season_boxplot_transform(
            season=doc.season,
            against=boxplot,
        )
    return "Success! Edited game " + str(doc.doc_id) + "."


@ml_api.delete('/delete-game/{doc_id}')
def delete_game(doc_id: int, client: MongoClient = Depends(get_dbm)):
    db = client.mildredleague
    collection = db.games
    doc = collection.find_one_and_delete({'_id': doc_id})
    # recalculate boxplot data, points for and against
    for boxplot in ['for', 'against']:
        season_boxplot_transform(
            season=doc.season,
            against=boxplot,
        )
    if doc:
        return "Success! Deleted game " + str(doc_id) + "."
    else:
        return "Something weird happened..."


@ml_api.get('/teams/all')
def get_all_teams(client: MongoClient = Depends(get_dbm)):
    db = client.mildredleague
    collection = db.teams
    # return full history of mildredleague teams
    data = list(collection.find())
    if not data:
        return "No data found!"
    else:
        return data


@ml_api.get('/games/all', response_model=List[MLGame])
def get_all_games(client: MongoClient = Depends(get_dbm)):
    db = client.mildredleague
    collection = db.games
    # return full history of mildredleague games
    data = list(collection.find())
    if not data:
        return "No data found!"
    else:
        return data


@ml_api.get('/games/{season}', response_model=List[MLGame])
def get_season_games(season: int, client: MongoClient = Depends(get_dbm)):
    db = client.mildredleague
    collection = db.games
    # return all results if no search_term
    data = list(collection.find({"season": season}))
    if not data:
        return "No data found!"
    else:
        return data


@ml_api.post('/add-note')
def add_note(doc: MLNote, client: MongoClient = Depends(get_dbm)):
    db = client.mildredleague
    collection = db.notes
    try:
        collection.insert_one(doc.dict(by_alias=True))
        return "Success! Added note " + str(doc.doc_id) + "."
    except pymongo.errors.DuplicateKeyError:
        return "Note " + str(doc.doc_id) + " already exists!"


@ml_api.get('/get-note/{doc_id}', response_model=MLNote)
def get_note(doc_id: int, client: MongoClient = Depends(get_dbm)):
    db = client.mildredleague
    collection = db.notes
    doc = list(collection.find({'_id': doc_id}))
    if doc:
        return doc[0]
    else:
        return "No document found!"


@ml_api.get('/notes/{season}', response_model=List[MLNote])
def get_season_notes(season: int, client: MongoClient = Depends(get_dbm)):
    db = client.mildredleague
    collection = db.notes
    # return all results if no search_term
    doc_list = list(collection.find({"season": season}))
    if doc_list:
        return doc_list
    else:
        return "No documents found!"


@ml_api.put('/edit-note')
def edit_note(doc: MLNote, client: MongoClient = Depends(get_dbm)):
    db = client.mildredleague
    collection = db.notes
    collection.replace_one({'_id': doc.doc_id}, doc)
    return "Success! Edited note " + str(doc.doc_id) + "."


@ml_api.delete('/delete-note/{doc_id}')
def delete_note(doc_id: int, client: MongoClient = Depends(get_dbm)):
    db = client.mildredleague
    collection = db.notes
    doc = collection.find_one_and_delete({'_id': doc_id})
    if doc:
        return "Success! Deleted game " + str(doc_id) + "."
    else:
        return "Something weird happened..."


@ml_api.get('/boxplot/{season}/{against}')
def season_boxplot_retrieve(season: int, against: Against, client: MongoClient = Depends(get_dbm)):
    db = client.mildredleague
    collection = getattr(db, against + str(season))
    data = list(collection.find({"name": {'$ne': 'Bye'}}))
    if data:
        return data
    else:
        return "No data found!"


def season_boxplot_transform(season, against):
    '''Call this function when games are added/edited/deleted.

    Boxplot data is transformed and cached so boxplots can
    be rendered more efficiently by end users.

    '''
    # read season and teams data from api
    games_data, response_code = get_season_games(season=season)
    teams_data, response_code = get_all_teams()
    season_df = pandas.DataFrame(games_data.json)
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
    if against == 'for':
        score_df = season_df[['a_nick', 'a_score_norm']].rename(
            columns={'a_nick': 'name', 'a_score_norm': 'score'},
        ).append(
            season_df[['h_nick', 'h_score_norm']].rename(
                columns={'h_nick': 'name', 'h_score_norm': 'score'},
            ),
            ignore_index=True,
        )
    # this code runs to analyze Points Against.
    if against == 'against':
        score_df = season_df[['a_nick', 'h_score_norm']].rename(
            columns={'a_nick': 'name', 'h_score_norm': 'score'},
        ).append(
            season_df[['h_nick', 'a_score_norm']].rename(
                columns={'h_nick': 'name', 'a_score_norm': 'score'},
            ),
            ignore_index=True,
        )
    # let's sort by playoff rank instead
    # read season file, but we only need nick_name, season, and playoff_rank
    ranking_df = pandas.DataFrame(teams_data.json)[['nick_name', 'season', 'playoff_rank']]
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
    client = get_dbm()
    db = client.mildredleague
    collection = getattr(db, against + str(season))
    if list(collection.find()) == doc_list:
        message, response_code = str(season) + against + " boxplot chart is already synced!"
    else:
        # if boxplots need to be recalculated, just wipe the collection and reinsert
        collection.delete_many({})
        collection.insert_many(doc_list)
        message, response_code = "Bulk delete and insert complete!"

    return message, response_code
