# import Python packages
from typing import Optional

# import third party packages
from fastapi import APIRouter, Depends
from pymongo import MongoClient

# import custom local stuff
from api.db import get_dbm


hysx_api = APIRouter(
    prefix="/haveyouseenx",
    tags=["haveyouseenx"],
)


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
    return results


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
