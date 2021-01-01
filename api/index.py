# import Python packages
import random
from typing import List

# import third party packages
from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
import pymongo
from pymongo import MongoClient
import seaborn

# import custom local stuff
from api.db import get_dbm
from api.users import oauth2_scheme


index_api = APIRouter(
    prefix="",
    tags=["meta"],
)


class Quote(BaseModel):
    doc_id: int = Field(alias="_id")
    quote_text: str
    quote_origin: str


@index_api.get('/quote/random', response_model=Quote)
async def random_quote(client: MongoClient = Depends(get_dbm)):
    db = client.quotes
    collection = db.quotes
    quote_count = collection.estimated_document_count()
    doc_id = random.randint(1, quote_count)
    quote = collection.find_one({"_id": doc_id})
    return quote


@index_api.get('/quote/all', response_model=List[Quote])
async def all_quotes(
    client: MongoClient = Depends(get_dbm),
):
    db = client.quotes
    collection = db.quotes
    doc = list(collection.find().sort("_id"))
    if doc:
        return doc
    else:
        return "No document found!"


@index_api.post('/quote', dependencies=[Depends(oauth2_scheme)])
async def add_quote(
    quote: Quote,
    client: MongoClient = Depends(get_dbm),
):
    db = client.quotes
    collection = db.quotes
    try:
        collection.insert_one(quote.dict(by_alias=True))
        # recalculate boxplot data for points for and against
        return "Success! Added quote " + str(quote.doc_id) + "."
    except pymongo.errors.DuplicateKeyError:
        return "Quote " + str(quote.doc_id) + " already exists!"


@index_api.get('/quote/{doc_id}', response_model=Quote)
async def get_quote(
    doc_id: int,
    client: MongoClient = Depends(get_dbm),
):
    db = client.quotes
    collection = db.quotes
    doc = list(collection.find({'_id': doc_id}))
    if doc:
        return doc[0]
    else:
        return "No document found!"


@index_api.put('/quote', dependencies=[Depends(oauth2_scheme)])
async def edit_quote(
    quote: Quote,
    client: MongoClient = Depends(get_dbm),
):
    db = client.quotes
    collection = db.quotes
    collection.replace_one({'_id': quote.doc_id}, quote.dict(by_alias=True))
    # recalculate boxplot data, points for and against
    return "Success! Edited quote " + str(quote.doc_id) + "."


@index_api.delete('/quote/{doc_id}', dependencies=[Depends(oauth2_scheme)])
async def delete_quote(
    doc_id: int,
    client: MongoClient = Depends(get_dbm),
):
    db = client.quotes
    collection = db.quotes
    doc = collection.find_one_and_delete({'_id': doc_id})
    # recalculate boxplot data, points for and against
    if doc:
        return "Success! Deleted quote " + str(doc_id) + "."
    else:
        return "Something weird happened..."
