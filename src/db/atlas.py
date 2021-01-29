# import third party packages
from motor.motor_asyncio import AsyncIOMotorClient


class MongoAtlas():
    client: AsyncIOMotorClient = None


atlas_object = MongoAtlas()


async def get_odm():
    return atlas_object.client


async def auto_increment_mongo(client, database, collection):
    """Retrieve the next _id for a given Mongo collection
    that's based on _id being a simple integer."""
    db = getattr(client, database)
    collection = getattr(db, collection)
    last_id_list = list(
        collection.aggregate([{"$group": {"_id": None, "last_id": {"$max": "$_id"}}}])
    )
    # if the list is empty, then the next id will be 1
    # otherwise it's the last id + 1
    if not last_id_list:
        next_id = 1
    else:
        next_id = last_id_list[0].get("last_id") + 1

    return next_id
