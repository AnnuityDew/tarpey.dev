# import third party packages
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from pymongo import MongoClient

# import custom local stuff
from api.db import get_dbm


ml_api = APIRouter(
    prefix="/mildredleague",
    tags=["mildredleague"],
)


class MLGame(BaseModel):
    _id: int
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
    _id: int
    season: int
    note: str


# declaring type of the client just helps with autocompletion.
@ml_api.get('/get-game/{game_id}')
async def get_game(game_id: int, client: MongoClient = Depends(get_dbm)):
    db = client.mildredleague
    collection = db.games
    doc = list(collection.find({'_id': game_id}))
    if doc:
        return doc[0], 200
    else:
        return "No document found!", 400
