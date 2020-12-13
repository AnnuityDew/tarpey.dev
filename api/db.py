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
