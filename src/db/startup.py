# import third party packages
from motor.motor_asyncio import AsyncIOMotorClient

# import custom local stuff
from instance.config import MONGO_CONNECT
from src.db.atlas import atlas_object


async def motor_startup():
    """Startup a motor client at app startup.

    https://github.com/markqiu/fastapi-mongodb-realworld-example-app/
    blob/master/app/db/mongodb_utils.py#L10
    """
    atlas_object.client = AsyncIOMotorClient(MONGO_CONNECT)


async def motor_shutdown():
    """Shutdown the motor client at app shutdown."""
    atlas_object.client.close()
