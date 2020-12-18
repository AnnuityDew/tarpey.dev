# import native Python packages
from enum import Enum
import json
from typing import List

# import third party packages
from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordBearer
import pandas
import plotly
import plotly.express as px
from pydantic import BaseModel, Field, validator
import pymongo
from pymongo import MongoClient

# import custom local stuff
from api.db import get_dbm


users_api = APIRouter(
    prefix="/users",
    tags=["users"],
)

# auth scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


class ApprovedUsers(str, Enum):
    TARPEY = "annuitydew"
    MATT = "matt"


class UserBase(BaseModel):
    username: ApprovedUsers

    @validator('username')
    def username_alphanumeric(cls, name):
        assert name.isalnum(), 'Username must be alphanumeric.'
        return name


class UserIn(UserBase):
    password: str


class UserOut(BaseModel):
    pass


class UserDB(BaseModel):
    hashed_password: str


@users_api.get('/test-token')
async def read_items(token: str = Depends(oauth2_scheme)):
    return {"token": token}
