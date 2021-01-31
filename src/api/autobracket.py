# import native Python packages
from datetime import date
from enum import Enum, IntEnum
from itertools import permutations, product
import orjson
from typing import List, Dict, Optional

# import third party packages
from fastapi import APIRouter, HTTPException, Depends
from motor.motor_asyncio import AsyncIOMotorClient
import numpy as np
import pandas
from pandas import StringDtype
import plotly
import plotly.express as px
from odmantic import AIOEngine, Field, Model, ObjectId
import requests

# import custom local stuff
from instance.config import FANTASY_DATA_KEY_FREE
from src.db.atlas import get_odm
from src.api.users import oauth2_scheme, UserOut


ab_api = APIRouter(
    prefix="/autobracket",
    tags=["autobracket"],
    dependencies=[Depends(oauth2_scheme)],
)


class FantasyDataSeason(str, Enum):
    PRIORSEASON1 = "2020"
    CURRENTSEASON = "2021"


class PlayerSeason(Model):
    StatID: int = Field(primary_field=True)
    TeamID: int
    PlayerID: int
    SeasonType: int
    Season: str
    Name: str
    Team: str
    Position: str
    Games: int
    FantasyPoints: float
    Minutes: int
    FieldGoalsMade: int
    FieldGoalsAttempted: int
    FieldGoalsPercentage: float
    TwoPointersMade: int
    TwoPointersAttempted: int
    TwoPointersPercentage: float
    ThreePointersMade: int
    ThreePointersAttempted: int
    ThreePointersPercentage: float
    FreeThrowsMade: int
    FreeThrowsAttempted: int
    FreeThrowsPercentage: float
    OffensiveRebounds: int
    DefensiveRebounds: int
    Rebounds: int
    Assists: int
    Steals: int
    BlockedShots: int
    Turnovers: int
    PersonalFouls: int
    Points: int
    FantasyPointsFanDuel: float
    FantasyPointsDraftKings: float


@ab_api.get("/stats/{season}/all")
async def get_season_players(
    season: FantasyDataSeason,
    client: AsyncIOMotorClient = Depends(get_odm),
):
    engine = AIOEngine(motor_client=client, database="autobracket")
    data = [
        player_season
        async for player_season in engine.find(
            PlayerSeason,
            (PlayerSeason.Season == season),
            sort=PlayerSeason.StatID,
        )
    ]

    if data:
        return data
    else:
        raise HTTPException(status_code=404, detail="No data found!")


@ab_api.get("/stats/{season}/{team}")
async def get_season_team_players(
    season: FantasyDataSeason,
    team: str,
    client: AsyncIOMotorClient = Depends(get_odm),
):
    engine = AIOEngine(motor_client=client, database="autobracket")
    data = [
        player_season
        async for player_season in engine.find(
            PlayerSeason,
            (PlayerSeason.Season == season) & (PlayerSeason.Team == team),
            sort=PlayerSeason.StatID,
        )
    ]

    if data:
        return data
    else:
        raise HTTPException(status_code=404, detail="No data found!")


@ab_api.get("/sim/{season}/{team_one}/{team_two}")
async def full_game_simulation(
    season: FantasyDataSeason,
    team_one: str,
    team_two: str,
    client: AsyncIOMotorClient = Depends(get_odm),
):
    engine = AIOEngine(motor_client=client, database="autobracket")
    matchup_data = [
        player_season
        async for player_season in engine.find(
            PlayerSeason,
            (PlayerSeason.Season == season)
            & ((PlayerSeason.Team == team_one) | (PlayerSeason.Team == team_two)),
            sort=(PlayerSeason.Team, PlayerSeason.StatID),
        )
    ]

    matchup_df = pandas.DataFrame(
        [player_season.doc() for player_season in matchup_data]
    )

    # assign columns for the simulated game stats
    matchup_df = matchup_df.assign(
        sim_seconds=0,
        sim_two_pointers_made=0,
        sim_two_pointers_attempted=0,
        sim_three_pointers_made=0,
        sim_three_pointers_attempted=0,
        sim_free_throws_made=0,
        sim_free_throws_attempted=0,
        sim_offensive_rebounds=0,
        sim_defensive_rebounds=0,
        sim_assists=0,
        sim_steals=0,
        sim_blocks=0,
        sim_turnovers=0,
        sim_fouls=0,
    )

    # minutes for each player, divided by total minutes played for each team
    player_minute_totals = matchup_df.groupby(["Team", "PlayerID"]).agg(
        {"Minutes": "sum"}
    )
    team_minute_totals = matchup_df.groupby(["Team"]).agg({"Minutes": "sum"})
    player_time_share = player_minute_totals.div(
        team_minute_totals, level="Team"
    ).rename(columns={"Minutes": "minute_dist"})
    matchup_df = matchup_df.merge(
        player_time_share,
        left_on=["Team", "PlayerID"],
        right_index=True,
        how="left",
    )

    # new numpy random number generator
    rng = np.random.default_rng()

    # determine first possession (simple 50/50 for now)
    matchup_list = team_minute_totals.index.to_list()
    possession_flag = rng.integers(2, size=1)[0]

    # game clock and shot clock reset flag
    time_remaining = 60 * 40
    shot_clock_reset = True

    # set index that will be the basis for updating box score.
    matchup_df.set_index(['Team', "PlayerID"], inplace=True)

    while time_remaining > 0:
        # who has the ball?
        offensive_team = matchup_list[possession_flag]
        defensive_team = matchup_list[(1 - possession_flag)]

        # possession length simulated here as uniform from 5-30 seconds, but
        # we definitely need to pull in some sort of tempo per team here.
        if shot_clock_reset:
            possession_length = min(
                [
                    (30 - 5) * rng.random() + 5,
                    time_remaining,
                ]
            )
        else:
            # shot clock didn't reset, so just use part of the leftover seconds
            # an improvement here would be to lower the likelihood of a successful
            # offensive possession
            possession_length = min(
                [
                    (30 - possession_length) * rng.random(),
                    time_remaining,
                ]
            )
            shot_clock_reset = not shot_clock_reset

        # pick 10 players for the current possession based on average time share
        on_floor_df = (
            matchup_df
            .groupby(level=0)
            .sample(n=5, replace=False, weights=matchup_df.minute_dist.to_list())
        )

        # add the possession length to the time played for each individual on the floor and update
        on_floor_df["sim_seconds"] = on_floor_df["sim_seconds"] + possession_length
        matchup_df.update(on_floor_df)

        # now, based on the 10 players on the floor, calculate probability of each event.
        # first, a steal check happens here. use steals per second over the season.
        # improvement: factor in the opponent's turnover statistics here.
        # steals per second times possession length to get the steal chance for this possession
        steal_probs = on_floor_df.groupby(level=[0,1]).agg(
            {
                "Steals": "sum",
                "Minutes": "sum",
                "sim_steals": "sum",
            }
        ).loc[[defensive_team]]
        steal_probs["steal_chance_pdf"] = (
            steal_probs["Steals"] / steal_probs["Minutes"] / 60 * possession_length
        )
        steal_probs["steal_chance_cdf"] = steal_probs.groupby(level=0).cumsum()[
            "steal_chance_pdf"
        ]

        # we also need turnover probabilities here
        turnover_probs = on_floor_df.groupby(level=[0,1]).agg(
            {
                "Turnovers": "sum",
                "Minutes": "sum",
                "sim_turnovers": "sum",
            }
        ).loc[[offensive_team]]
        turnover_probs["turnover_chance_pdf"] = (
            turnover_probs["Turnovers"]
            / turnover_probs["Minutes"]
            / 60
            * possession_length
        )
        turnover_probs["turnover_chance_cdf"] = turnover_probs.groupby(
            level=0
        ).cumsum()["turnover_chance_pdf"]

        # the steal/turnover check! we're modeling them as independent.
        # (right now it's possible that a turnover in a given possession
        # will always be a steal, if turnover_chance is less than steal_chance.)
        steal_turnover_success = rng.random()
        steal_chance = steal_probs.loc[defensive_team].steal_chance_cdf.max()
        turnover_chance = turnover_probs.loc[offensive_team].turnover_chance_cdf.max()

        # if there's a successful steal, credit the steal and turnover, then flip possession and restart loop!
        if steal_turnover_success < steal_chance:
            # who got the steal?
            steal_player = steal_probs.sample(
                n=1, weights=steal_probs.steal_chance_pdf
            )
            steal_player["sim_steals"] = steal_player["sim_steals"] + 1
            matchup_df.update(steal_player)

            # who committed the turnover?
            turnover_player = turnover_probs.sample(
                n=1, weights=turnover_probs.turnover_chance_pdf
            )
            turnover_player["sim_turnovers"] = turnover_player["sim_turnovers"] + 1
            matchup_df.update(turnover_player)

            # change clock, give ball to other team, reset loop
            time_remaining -= possession_length
            possession_flag = 1 - possession_flag
            continue
        # if there's a turnover, credit the turnover, then flip possession and restart loop!
        elif steal_turnover_success < turnover_chance:
            # who committed the turnover?
            turnover_player = turnover_probs.sample(
                n=1, weights=turnover_probs.turnover_chance_pdf
            )
            turnover_player["sim_turnovers"] = turnover_player["sim_turnovers"] + 1
            # update box score, change clock, give ball to other team, reset loop
            matchup_df.update(turnover_player)
            time_remaining -= possession_length
            possession_flag = 1 - possession_flag
            continue

        # time to model shot attempts. if there's no steal or turnover,
        # a shot is the only other outcome, so we can simply model who's
        # gonna take it and what kind of shot it will be.
        shot_probs = on_floor_df.groupby(level=[0,1]).agg(
            {
                "TwoPointersAttempted": "sum",
                "TwoPointersMade": "sum",
                "ThreePointersAttempted": "sum",
                "ThreePointersMade": "sum",
                "FieldGoalsAttempted": "sum",
                "FieldGoalsMade": "sum",
                'sim_two_pointers_made': 'sum',
                'sim_two_pointers_attempted': 'sum',
                'sim_three_pointers_made': 'sum',
                'sim_three_pointers_attempted': 'sum',
            }
        ).loc[[offensive_team]]
        team_shot_prob = shot_probs.groupby(level=0).sum()
        shot_share = shot_probs.div(
            team_shot_prob, level="Team"
        )
        shot_probs['field_goal_pdf'] = shot_share['FieldGoalsAttempted']
        
        # identify the shooter
        shooting_player = shot_probs.sample(n=1, weights=shot_probs.field_goal_pdf)

        # determine 2pt attempt or 3pt attempt
        shooting_player = shooting_player.assign(
            two_attempt_chance=lambda x: x.TwoPointersAttempted / x.FieldGoalsAttempted,
            two_chance=lambda x: x.TwoPointersMade / x.TwoPointersAttempted,
            three_chance=lambda x: x.ThreePointersMade / x.ThreePointersAttempted,
        )

        # if a defensive player blocks, 50/50 chance to be a turnover.
        # using blocks per second over the season.
        # we're either crediting miss+block, or miss+block+rebound.
        block_probs = on_floor_df.groupby(level=[0,1]).agg(
            {
                "BlockedShots": 'sum',
                "Minutes": 'sum',
                'sim_blocks': 'sum',
            }
        ).loc[[defensive_team]]
        block_probs["block_chance_pdf"] = (
            block_probs["BlockedShots"] / block_probs["Minutes"] / 60 * possession_length
        )
        block_probs["block_chance_cdf"] = block_probs.groupby(level=0).cumsum()[
            "block_chance_pdf"
        ]

        # block check!
        block_success = rng.random()
        block_chance = block_probs.block_chance_cdf.max()

        # the shot type check!
        two_or_three = rng.random()

        if block_success < block_chance:
            # who got the block?
            blocking_player = block_probs.sample(
                n=1, weights=block_probs.block_chance_pdf
            )
            blocking_player['sim_blocks'] = blocking_player['sim_blocks'] + 1
            matchup_df.update(blocking_player)

            if two_or_three < shooting_player.two_attempt_chance.values[0]:
                # credit the shooter with a 2pt attempt
                shooting_player['sim_two_pointers_attempted'] = (
                    shooting_player['sim_two_pointers_attempted'] + 1
                )
            else:
                # credit the shooter with a 3pt attempt
                shooting_player['sim_three_pointers_attempted'] = (
                    shooting_player['sim_three_pointers_attempted'] + 1
                )
            matchup_df.update(shooting_player)

            # block out of bounds check! this is 50/50 for now.
            block_oob_check = rng.integers(2, size=1)[0]

            if block_oob_check == 1:
                # no change of possession, don't reset shot clock
                time_remaining -= possession_length
                shot_clock_reset = not shot_clock_reset
                continue
            else:
                # rebound logic
                offensive_rebound_probs = on_floor_df.groupby(["Team", "PlayerID"]).agg(
                    {
                        "OffensiveRebounds": 'sum',
                        'sim_offensive_rebounds': 'sum',
                    }
                ).loc[[offensive_team]]
                defensive_rebound_probs = on_floor_df.groupby(["Team", "PlayerID"]).agg(
                    {
                        "DefensiveRebounds": 'sum',
                        'sim_defensive_rebounds': 'sum',
                    }
                ).loc[[defensive_team]]
                team_off_reb_total = offensive_rebound_probs.groupby(level=0).sum()
                team_def_reb_total = defensive_rebound_probs.groupby(level=0).sum()
                rebound_denominator = (
                    team_off_reb_total['OffensiveRebounds'][0] +
                    team_def_reb_total['DefensiveRebounds'][0]
                )

                # rebound type check!
                off_reb_success = rng.random()
                off_reb_chance = team_off_reb_total['OffensiveRebounds'][0] / rebound_denominator

                if off_reb_chance < off_reb_success:
                    # who got the rebound?
                    off_reb_share = offensive_rebound_probs.div(
                        team_off_reb_total, level="Team"
                    )
                    offensive_rebound_probs['off_reb_pdf'] = off_reb_share['OffensiveRebounds']
                    rebounding_player = offensive_rebound_probs.sample(n=1, weights=offensive_rebound_probs.off_reb_pdf)
                    rebounding_player['sim_offensive_rebounds'] = rebounding_player['sim_offensive_rebounds'] + 1
                    matchup_df.update(rebounding_player)

                    # no change of possession, don't reset shot clock
                    time_remaining -= possession_length
                    shot_clock_reset = not shot_clock_reset
                    continue
                else:
                    # who got the rebound?
                    def_reb_share = defensive_rebound_probs.div(
                        team_def_reb_total, level="Team"
                    )
                    defensive_rebound_probs['def_reb_pdf'] = def_reb_share['DefensiveRebounds']
                    rebounding_player = defensive_rebound_probs.sample(n=1, weights=defensive_rebound_probs.def_reb_pdf)
                    rebounding_player['sim_defensive_rebounds'] = rebounding_player['sim_defensive_rebounds'] + 1
                    matchup_df.update(rebounding_player)

                    # update clock, change of possession, reset loop
                    time_remaining -= possession_length
                    possession_flag = 1 - possession_flag
                    continue

        # if we've made it this far, the shot was not blocked.
        # but did it go in? and was there a foul?
        foul_probs = on_floor_df.groupby(level=[0,1]).agg(
            {
                "PersonalFouls": "sum",
                "Minutes": "sum",
                "sim_fouls": "sum",
            }
        ).loc[[defensive_team]]
        foul_probs["foul_chance_pdf"] = (
            foul_probs["PersonalFouls"] / foul_probs["Minutes"] / 60 * possession_length
        )
        foul_probs["foul_chance_cdf"] = foul_probs.groupby(level=0).cumsum()[
            "foul_chance_pdf"
        ]
        
        # defensive foul check! (potential improvement, offensive fouls)
        foul_chance = foul_probs.loc[defensive_team].foul_chance_cdf.max()
        foul_occurred = rng.random()

        if two_or_three < shooting_player.two_attempt_chance.values[0]:
            # check two point probability
            two_success = rng.random()
            if two_success < shooting_player.two_chance.values[0]:
                # credit the shooter with a 2pt attempt and make
                shooting_player['sim_two_pointers_attempted'] = (
                    shooting_player['sim_two_pointers_attempted'] + 1
                )
                shooting_player['sim_two_pointers_made'] = (
                    shooting_player['sim_two_pointers_made'] + 1
                )
                matchup_df.update(shooting_player)
                # add assisting player and foul stuff here
                # change clock, give ball to other team, reset loop
                time_remaining -= possession_length
                possession_flag = 1 - possession_flag
                continue
            
            else:
                shooting_player['sim_two_pointers_attempted'] = (
                    shooting_player['sim_two_pointers_attempted'] + 1
                )
                matchup_df.update(shooting_player)
            # add missed shot stuff 
            # (foul or rebound?)
            # attempt doesn't count on a foul!
            

        else:
            # check three point probability
            three_success = rng.random()
            if three_success < shooting_player.three_chance.values[0]:
                # credit the shooter with a 3pt attempt and make
                shooting_player['sim_three_pointers_attempted'] = (
                    shooting_player['sim_three_pointers_attempted'] + 1
                )
                shooting_player['sim_three_pointers_made'] = (
                    shooting_player['sim_three_pointers_made'] + 1
                )
                matchup_df.update(shooting_player)
                # add assisting player and foul stuff here
                # change clock, give ball to other team, reset loop
                time_remaining -= possession_length
                possession_flag = 1 - possession_flag
                continue

            else:
                shooting_player['sim_three_pointers_attempted'] = (
                    shooting_player['sim_three_pointers_attempted'] + 1
                )
                matchup_df.update(shooting_player)
            # add missed shot stuff 
            # (foul or rebound?)
            # attempt doesn't count on a foul!

        time_remaining -= possession_length
        possession_flag = 1 - possession_flag
        print(time_remaining)

    # calculate points!
    matchup_df = matchup_df.assign(
        sim_points=lambda x: x.sim_two_pointers_made * 2 + x.sim_three_pointers_made * 3
    )

    box_score_df = matchup_df[
        [
            "Name",
            "Position",
            "sim_seconds",
            'sim_two_pointers_made',
            'sim_two_pointers_attempted',
            'sim_three_pointers_made',
            'sim_three_pointers_attempted',
            # 'sim_free_throws_made',
            # 'sim_free_throws_attempted',
            'sim_offensive_rebounds',
            'sim_defensive_rebounds',
            # 'sim_assists',
            "sim_steals",
            'sim_blocks',
            "sim_turnovers",
            # 'sim_fouls',
            'sim_points',
        ]
    ]

    # calculate totals
    box_score_df = box_score_df.assign(sim_minutes=lambda x: x.sim_seconds / 60)

    # aggregate team box score
    team_box_score_df = box_score_df.groupby(level=0).sum()

    box_score_json = orjson.loads(box_score_df.to_json(orient="records"))
    team_box_score_json = orjson.loads(team_box_score_df.to_json(orient="index"))

    return [team_box_score_json, box_score_json]


@ab_api.get("/FantasyDataRefresh/PlayerGameDay/{game_year}/{game_month}/{game_day}")
async def refresh_fd_player_games(
    game_year: int,
    game_month: int,
    game_day: int,
    client: AsyncIOMotorClient = Depends(get_odm),
):
    try:
        game_date = date(game_year, game_month, game_day)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"API error: {e}")

    requested_date = game_date.strftime("%Y-%b-%d")

    r = requests.get(
        f"https://api.sportsdata.io/api/cbb/fantasy/json/PlayerGameStatsByDate/{requested_date}"
        + "?key="
        + FANTASY_DATA_KEY_FREE
    )

    engine = AIOEngine(motor_client=client, database="autobracket")

    return {"message": "Mongo refresh complete!"}


@ab_api.get("/FantasyDataRefresh/PlayerSeason/{season}")
async def refresh_fd_player_season(
    season: FantasyDataSeason,
    client: AsyncIOMotorClient = Depends(get_odm),
):
    r = requests.get(
        f"https://api.sportsdata.io/api/cbb/fantasy/json/PlayerSeasonStats/{season}"
        + "?key="
        + FANTASY_DATA_KEY_FREE
    )

    engine = AIOEngine(motor_client=client, database="autobracket")

    # data manipulation is easier in Pandas!
    player_season_df = pandas.DataFrame(r.json())

    # season should be string (ex: 2020POST). then convert other columns.
    # if we do the opposite order the Season column will throw an error.
    # can't go directly from int to str - you'll get an error! map first
    player_season_df["Season"] = player_season_df["Season"].map(str).astype("string")
    player_season_df = player_season_df.convert_dtypes()

    # position is None for about 3200 players...fill with "Not Found"
    player_season_df["Position"] = player_season_df["Position"].fillna("Not Found")

    # back to json for writing to DB
    p = orjson.loads(player_season_df.to_json(orient="records"))
    await engine.save_all([PlayerSeason(**doc) for doc in p])

    return {"message": "Mongo refresh complete!"}


@ab_api.get("/FantasyDataRefresh/PlayerSeasonTeam/{season}/{team}")
async def refresh_fd_player_season_team(
    season: FantasyDataSeason,
    team: str,
):
    r = requests.get(
        f"https://api.sportsdata.io/api/cbb/fantasy/json/PlayerSeasonStatsByTeam/{season}/{team}"
        + "?key="
        + FANTASY_DATA_KEY_FREE
    )

    return {"message": "Mongo refresh complete!"}
