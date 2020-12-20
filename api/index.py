# import Python packages
import random

# import third party packages
from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
import pymongo
from pymongo import MongoClient

# import custom local stuff
from api.db import get_dbm
from api.users import oauth2_scheme


index_api = APIRouter(
    prefix="",
    tags=["meta"],
)


class RandomQuote(BaseModel):
    doc_id: int = Field(alias="_id")
    quote_text: str
    quote_origin: str


@index_api.get('/random-quote', response_model=RandomQuote)
async def random_quote(client: MongoClient = Depends(get_dbm)):
    db = client.quotes
    collection = db.quotes
    quote_count = collection.estimated_document_count()
    doc_id = str(random.randint(1, quote_count))
    quote = collection.find_one({"_id": doc_id})
    return quote


@index_api.post('/add-quote')
async def add_quote(
    quote: RandomQuote,
    client: MongoClient = Depends(get_dbm),
    token: str = Depends(oauth2_scheme),
):
    db = client.quotes
    collection = db.quotes
    try:
        collection.insert_one(quote.dict(by_alias=True))
        # recalculate boxplot data for points for and against
        return "Success! Added quote " + str(quote.doc_id) + "."
    except pymongo.errors.DuplicateKeyError:
        return "Quote " + str(quote.doc_id) + " already exists!"
