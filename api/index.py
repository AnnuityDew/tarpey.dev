# import Python packages
import random

# import third party packages
from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
import pymongo
from pymongo import MongoClient

# import custom local stuff
from api.db import get_dbm


index_api = APIRouter(
    prefix="",
    tags=["meta"],
)


class RandomQuote(BaseModel):
    quote_id: int = Field(None, alias='_id')
    quote_text: str
    quote_origin: str


@index_api.get('/random-quote')
async def random_quote(client: MongoClient = Depends(get_dbm)):
    db = client.quotes
    collection = db.quotes
    quote_count = collection.estimated_document_count()
    quote_id = str(random.randint(1, quote_count))
    quote = collection.find_one({"_id": quote_id})
    return quote


@index_api.post('/add-quote')
async def add_quote(quote: RandomQuote, client: MongoClient = Depends(get_dbm)):
    db = client.quotes
    collection = db.quotes
    try:
        collection.insert_one(quote.__dict__)
        # recalculate boxplot data for points for and against
        return "Success! Added quote " + str(quote.quote_id) + ".", 200
    except pymongo.errors.DuplicateKeyError:
        return "Quote " + str(quote.quote_id) + " already exists!", 400
