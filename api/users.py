# import native Python packages
from enum import Enum
import json
from typing import List

# import third party packages
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import (
    OAuth2PasswordBearer, OAuth2PasswordRequestForm
)
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
    disabled: Optional[bool] = None

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


@users_api.post("/token")
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    client: MongoClient = Depends(get_dbm),
    ):
    db = client.users
    collection = db.users

    user_dict = collection.find_one({"_id": form_data.username})
    if not user_dict:
        raise HTTPException(
            status_code=400,
            detail="Incorrect username or password!",
        )
    # **user_dict passes in keys and values as model arguments
    user = UserDB(**user_dict)

    hashed_password = fake_hash_password(form_data.password)
    if hashed_password != user.hashed_password:
        raise HTTPException(
            status_code=400,
            detail="Incorrect username or password!",
        )
    
    # OAuth2 spec
    return {"access_token": user.username, "token_type": "bearer"}


@users_api.get("/me")
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    return current_user


async def get_current_active_user(current_user: User = Depends(get_current_user)):
    if current_user.disabled:
        raise HTTPException(
            status_code=400,
            detail="Inactive user!"
        )
    return current_user


async def get_current_user(token: str = Depends(oauth2_scheme)):
    user = fake_decode_token(token)
    if not user:
        # OAuth2 spec
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials!",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


def fake_decode_token(token):
    return User(
        username=token + "fakedecoded",
    )
