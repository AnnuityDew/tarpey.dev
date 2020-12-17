# import third party packages
from fastapi import APIRouter, Depends
from pymongo import MongoClient

# import custom local stuff
from api.db import get_dbm


ml_api = APIRouter(
    prefix="/mildredleague",
    tags=["mildredleague"],
)


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
