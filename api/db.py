# import third party packages
from pymongo import MongoClient

# import custom local stuff
from instance.config import MONGO_CONNECT


async def get_dbm():
    client = MongoClient(MONGO_CONNECT)
    try:
        yield client
    finally:
        client.close()


async def auto_increment_mongo(database, collection):
    '''Retrieve the next _id for a given Mongo collection.'''
    client = get_dbm()
    db = getattr(client, database)
    collection = getattr(db, collection)
    last_id_list = list(
        collection.aggregate([{
            '$group': {
                '_id': None,
                'last_id': {'$max': '$_id'}
            }
        }])
    )
    # if the list is empty, then the next id will be 1
    # otherwise it's the last id + 1
    if not last_id_list:
        next_id = 1
    else:
        next_id = last_id_list[0].get('last_id') + 1

    return next_id
