# import Python packages
import random

# import third party packages
from fastapi import APIRouter, Depends
from pymongo import MongoClient

# import custom local stuff
from api.db import get_dbm


index_api = APIRouter(
    prefix="",
    tags=["meta"],
)


@index_api.get('/random-quote')
async def random_quote(client: MongoClient = Depends(get_dbm)):
    db = client.quotes
    quote_count = db.quotes.estimated_document_count()
    quote_id = str(random.randint(1, quote_count))
    quote = db.quotes.find_one({"_id": quote_id})
    return quote
