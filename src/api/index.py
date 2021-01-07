# import Python packages
import random
from typing import List

# import third party packages
from fastapi import APIRouter, Depends
from fastapi.exceptions import HTTPException
from pydantic import BaseModel, Field
import pymongo
from pymongo import MongoClient
import seaborn

# import custom local stuff
from src.api.db import get_dbm
from src.api.users import oauth2_scheme


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
    doc_list: List[Quote],
    client: MongoClient = Depends(get_dbm),
):
    db = client.quotes
    collection = db.quotes
    try:
        insert_many_result = collection.insert_many([doc.dict(by_alias=True) for doc in doc_list])
        return {
            'inserted_ids': insert_many_result.inserted_ids,
            'doc_list': doc_list,
        }
    except pymongo.errors.DuplicateKeyError:
        raise HTTPException(status_code=409, detail="Duplicate ID!")


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
        raise HTTPException(status_code=404, detail="No data found!")


@index_api.put('/quote', dependencies=[Depends(oauth2_scheme)])
async def edit_quote(
    doc: Quote,
    client: MongoClient = Depends(get_dbm),
):
    db = client.quotes
    collection = db.quotes
    update_result = collection.replace_one({'_id': doc.doc_id}, doc.dict(by_alias=True))
    return {
        'doc': doc,
        'modified_count': update_result.modified_count,
    }


@index_api.delete('/quote/{doc_id}', dependencies=[Depends(oauth2_scheme)])
async def delete_quote(
    doc_id: int,
    client: MongoClient = Depends(get_dbm),
):
    db = client.quotes
    collection = db.quotes
    doc = collection.find_one_and_delete({'_id': doc_id})
    if doc:
        return {
            'doc': doc,
        }
    else:
        raise HTTPException(status_code=404, detail="No data found!")
