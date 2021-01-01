# import native Python packages
from datetime import timedelta
from enum import Enum
from typing import Optional
from fastapi.security.oauth2 import OAuth2PasswordBearer

# import third party packages
import jwt
from fastapi import APIRouter, Depends, HTTPException, Request, status
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


# security scheme.
# we're overwriting the __call__ method of LoginManager
# from fastapi_login to check for headers first, and only
# check for cookie if no headers exist. it's the opposite
# order of fastapi_login essentially, so the docs will work
# correctly.
class LoginManagerReversed(LoginManager):
    def _token_from_cookie(self, request: Request) -> Optional[str]:
        """
        Simplifying the FastAPI cookie method here. Rather than raise an unnecessary
        exception, if there is no cookie we simply return None and move on to checking
        """
        token = request.cookies.get(self.cookie_name)

        # if not token and self.auto_error:
            # this is the standard exception as raised
            # by the parent class
            # raise InvalidCredentialsException

        return token if token else None

    async def __call__(self, request: Request):
        """
        Couple extra lines added to the __call__ function to add username
        to the request state (so it can be accessed on every page to say hello).
        """
        token = None
        if self.use_cookie:
            token = self._token_from_cookie(request)
                
        if token is None and self.use_header:
            token = await super(LoginManager, self).__call__(request)

        if token is not None:
            active_user = await self.get_current_user(token)
            request.state.active_user = active_user.username.value
            return active_user

        # No token is present in the request and no Exception has been raised (auto_error=False)
        raise self.not_authenticated_exception


oauth2_scheme = LoginManagerReversed(
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


@users_api.post("/", response_model=UserOut)
async def create_user(
    form_data: OAuth2PasswordRequestForm = Depends(),
    client: MongoClient = Depends(get_dbm),
):
    db = client.users
    collection = db.users

    try:
        collection.insert_one({
            "_id": form_data.username,
            "hashed_password": get_password_hash(form_data.password)
        })
    except pymongo.errors.DuplicateKeyError:
        raise HTTPException(
            status_code=400,
            detail=f"{form_data.username} is already registered!"
        )

    return {'username': form_data.username}


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
async def read_self(current_user: UserOut = Depends(oauth2_scheme)):
    return current_user


@users_api.delete("/me")
async def delete_self(
    client: MongoClient = Depends(get_dbm),
    current_user: UserOut = Depends(oauth2_scheme),
):
    db = client.users
    collection = db.users
    doc = collection.find_one_and_delete({'_id': current_user.username})
    if doc:
        return "Success! Deleted user " + str(current_user.username) + "."
    else:
        return "Something weird happened..."


@users_api.patch("/password", response_model=UserOut)
async def change_password(
    updated_user: UserIn,
    current_user: UserOut = Depends(oauth2_scheme),
    client: MongoClient = Depends(get_dbm),
):
    db = client.users
    collection = db.users
    collection.update_one(
        {"_id": current_user.username},
        {'$set': {"hashed_password": get_password_hash(updated_user.password)}},
    )

    return updated_user


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
    return_user_only = False
    if client is None:
        return_user_only = True
        client = get_dbm_no_close()
    db = client.users
    collection = db.users
    user_dict = collection.find_one({"_id": username})
    client.close()
    # if calling through FastAPI login, just return username
    # otherwise, return hashed password so it can be verified
    if user_dict:
        if return_user_only:
            return UserOut(**user_dict)
        else:
            return UserDB(**user_dict)
