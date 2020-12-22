# import native Python packages
from datetime import timedelta
from enum import Enum
from typing import Optional

# import third party packages
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from fastapi_login import LoginManager
from passlib.context import CryptContext
from pydantic import BaseModel, Field, validator
import pymongo
from pymongo import MongoClient

# import custom local stuff
from api.db import get_dbm, get_dbm_no_close
from instance.config import (
    SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES
)


users_api = APIRouter(
    prefix="/users",
    tags=["users"],
)

# security schemes
oauth2_scheme = LoginManager(
    SECRET_KEY,
    tokenUrl='users/token',
    algorithm=ALGORITHM,
    use_cookie=True,
)
oauth2_scheme.cookie_name = 'Authorization'
password_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class ApprovedUsers(str, Enum): 
    TARPEY = "annuitydew"
    MATT = "matt"


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Optional[str] = None


class UserBase(BaseModel):
    username: ApprovedUsers = Field(..., alias='_id')
    disabled: Optional[bool] = False

    @validator('username')
    def username_alphanumeric(cls, name):
        assert name.isalnum(), 'Username must be alphanumeric.'
        return name

    class Config:
        # with this setting validation doesn't fail for username.
        # we use username as the MongoDB _id, so _id is an alias
        allow_population_by_field_name = True


class UserIn(UserBase):
    password: str

    @validator('password')
    def password_alphanumeric(cls, pw):
        assert pw.isalnum(), 'Password must be alphanumeric.'
        return pw


class UserOut(UserBase):
    pass


class UserDB(UserBase):
    hashed_password: str


@users_api.post("/token", response_model=Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    client: MongoClient = Depends(get_dbm),
):
    user = authenticate_user(
        form_data.username,
        form_data.password,
        client,
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password!",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    # sub should be unique across entire application, and it
    # should be a string. user.username could instead have a
    # bot prefix for "bot:x" access to do something.
    access_token = oauth2_scheme.create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires,
    )
    return {"access_token": access_token, "token_type": "bearer"}


@users_api.get("/me", response_model=UserOut)
async def read_self(current_user: UserOut = Depends(oauth2_scheme.get_current_user)):
    return current_user


@users_api.post("/", response_model=UserOut)
async def create_user(
    new_user: UserIn,
    client: MongoClient = Depends(get_dbm),
):
    db = client.users
    collection = db.users

    try:
        collection.insert_one({
            "_id": new_user.username,
            "hashed_password": get_password_hash(new_user.password)
        })
    except pymongo.errors.DuplicateKeyError:
        raise HTTPException(
            status_code=400,
            detail=f"{new_user.username} is already registered!"
        )

    return new_user


def verify_password(plain_password, hashed_password):
    return password_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    return password_context.hash(password)


def authenticate_user(username: str, password: str, client: MongoClient):
    user = get_user(username, client)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user


@oauth2_scheme.user_loader
def get_user(username: str, client: MongoClient = None):
    # this is where rubber meets the road between tiangolo's tutorial
    # and the fastapi_login docs. the mongo client is passed through
    # when FastAPI calls it. for fastapi_login's decorator, which only
    # passes in the username value of the decoded token, we go out and
    # get the client separately.
    # we could move the FastAPI code to authenticate_user to keep
    # these two more separate, but it doesn't seem necessary since
    # the password gets chopped off by the UserOut model in the /me
    # endpoint.
    if client is None:
        client = get_dbm_no_close()
    db = client.users
    collection = db.users
    user_dict = collection.find_one({"_id": username})
    # since we're not calling this with yield, need to
    # manually close mongo here
    client.close()
    if user_dict:
        return UserDB(**user_dict)
