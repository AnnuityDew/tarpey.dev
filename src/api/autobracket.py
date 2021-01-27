# import native Python packages
from enum import Enum, IntEnum
from itertools import permutations, product
import json
from typing import List, Dict, Optional

# import third party packages
from fastapi import APIRouter, HTTPException, Depends
from motor.motor_asyncio import AsyncIOMotorClient
import pandas
import plotly
import plotly.express as px
from odmantic import AIOEngine, Field, Model, ObjectId
import requests

# import custom local stuff
from instance.config import FANTASY_DATA_KEY_FREE
from src.api.db import get_odm
from src.api.users import oauth2_scheme, UserOut


ab_api = APIRouter(
    prefix="/autobracket",
    tags=["autobracket"],
    dependencies=[Depends(oauth2_scheme)],
)


class FantasyDataSeason(str, Enum):
    CURRENTSEASON = '2021'
    PRIORSEASON1 = '2020'


@ab_api.get("/test-player-game")
async def get_fd_player_game(requested_date: str):
    r = requests.get(
        f"https://api.sportsdata.io/api/cbb/fantasy/json/PlayerGameStatsByDate/{requested_date}"
        + "?key="
        + FANTASY_DATA_KEY_FREE
    )
    return r.json()


@ab_api.get("/test-player-season")
async def get_fd_player_season(season: FantasyDataSeason):
    r = requests.get(
        f"https://api.sportsdata.io/api/cbb/fantasy/json/PlayerSeasonStats/{season}"
        + "?key="
        + FANTASY_DATA_KEY_FREE
    )
    return r.json()


@ab_api.get("/test-player-season-team")
async def get_fd_player_season_team(season: FantasyDataSeason, team: str):
    r = requests.get(
        f"https://api.sportsdata.io/api/cbb/fantasy/json/PlayerSeasonStatsByTeam/{season}/{team}"
        + "?key="
        + FANTASY_DATA_KEY_FREE
    )
    return r
