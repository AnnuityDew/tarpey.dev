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

# import custom local stuff
from src.db.atlas import get_odm
from src.api.users import oauth2_scheme, UserOut


ml_api = APIRouter(
    prefix="/mildredleague",
    tags=["mildredleague"],
)


class Against(str, Enum):
    AGAINST = "against"
    FOR = "for"


class NickName(str, Enum):
    TARPEY = "Tarpey"
    CHRISTIAN = "Christian"
    NEEL = "Neel"
    BRANDO = "Brando"
    DEBBIE = "Debbie"
    DANNY = "Danny"
    MILDRED = "Mildred"
    HARDY = "Hardy"
    TOMMY = "Tommy"
    BRYANT = "Bryant"
    KINDY = "Kindy"
    SENDZIK = "Sendzik"
    SAMIK = "Samik"
    STEPHANIE = "Stephanie"
    DEBSKI = "Debski"
    BEN = "Ben"
    ARTHUR = "Arthur"
    CONTI = "Conti"
    FONTI = "Fonti"
    FRANK = "Frank"
    MIKE = "mballen"
    PATRICK = "Patrick"
    CHARLES = "Charles"
    JAKE = "Jake"
    BRAD = "Brad"
    BYE = "Bye"


class MLSeason(IntEnum):
    SEASON1 = 2013
    SEASON2 = 2014
    SEASON3 = 2015
    SEASON4 = 2016
    SEASON5 = 2017
    SEASON6 = 2018
    SEASON7 = 2019
    SEASON8 = 2020


class MLPlayoff(IntEnum):
    REGULAR = 0
    PLAYOFF = 1
    LOSERS = 2


class MLGame(Model):
    away: str
    a_nick: NickName
    a_score: float
    home: str
    h_nick: NickName
    h_score: float
    week_s: int
    week_e: int
    season: MLSeason
    playoff: MLPlayoff


class MLGamePatch(Model):
    away: Optional[str]
    a_nick: Optional[NickName]
    a_score: Optional[float]
    home: Optional[str]
    h_nick: Optional[NickName]
    h_score: Optional[float]
    week_s: Optional[int]
    week_e: Optional[int]
    season: Optional[MLSeason]
    playoff: Optional[MLPlayoff]


class MLTeam(Model):
    division: str
    full_name: str
    nick_name: NickName
    season: MLSeason
    playoff_rank: int
    active: bool


class MLTeamPatch(Model):
    division: Optional[str]
    full_name: Optional[str]
    nick_name: Optional[NickName]
    season: Optional[MLSeason]
    playoff_rank: Optional[int]
    active: Optional[bool]


class MLNote(Model):
    season: MLSeason
    note: str


class MLNotePatch(Model):
    season: Optional[MLSeason]
    note: Optional[str]


class MLTableTransform(Model):
    season: MLSeason
    playoff: MLPlayoff
    columns: List
    data: List


class MLBoxplotTransform(Model):
    season: MLSeason
    for_data: Dict
    against_data: Dict


class MLTable(pandas.DataFrame):
    def copy(self):
        copy_df = super().copy()
        return MLTable(copy_df)

    def merge_with_teams(self, teams_df):
        merged_df = self.copy()
        # merge on the away side
        teams_df.rename(columns={"nick_name": "a_nick"}, inplace=True)
        merged_df = merged_df.merge(
            teams_df[["a_nick", "season", "division"]],
            on=["a_nick", "season"],
            how="left",
        )
        merged_df.rename(columns={"division": "a_division"}, inplace=True)
        # merge on the home side
        teams_df.rename(columns={"a_nick": "h_nick"}, inplace=True)
        merged_df = merged_df.merge(
            teams_df[["h_nick", "season", "division"]],
            on=["h_nick", "season"],
            how="left",
        )
        merged_df.rename(columns={"division": "h_division"}, inplace=True)
        # reclass here since merge returns a vanilla DF
        return merged_df

    def normalize_games(self):
        normalized_df = self.copy()
        # which team won?
        normalized_df["a_win"] = 0
        normalized_df["h_win"] = 0
        normalized_df["a_tie"] = 0
        normalized_df["h_tie"] = 0
        # away win
        normalized_df.loc[normalized_df.a_score > normalized_df.h_score, "a_win"] = 1
        # home win
        normalized_df.loc[normalized_df.a_score < normalized_df.h_score, "h_win"] = 1
        # tie
        normalized_df.loc[
            normalized_df.a_score == normalized_df.h_score, ["a_tie", "h_tie"]
        ] = 1
        # normalized score columns for two-week playoff games
        normalized_df["a_score_norm"] = normalized_df["a_score"] / (
            normalized_df["week_e"] - normalized_df["week_s"] + 1
        )
        normalized_df["h_score_norm"] = normalized_df["h_score"] / (
            normalized_df["week_e"] - normalized_df["week_s"] + 1
        )
        # margin = home - away
        normalized_df["h_margin"] = (
            normalized_df["h_score_norm"] - normalized_df["a_score_norm"]
        )

        return normalized_df

    def calc_records(self, teams_df, divisions=True):
        if divisions:
            a_index = ["a_division", "a_nick"]
            h_index = ["h_division", "h_nick"]
            a_rename = {"a_nick": "nick_name", "a_division": "division"}
            h_rename = {"h_nick": "nick_name", "h_division": "division"}
        else:
            a_index = ["a_nick"]
            h_index = ["h_nick"]
            a_rename = {"a_nick": "nick_name"}
            h_rename = {"h_nick": "nick_name"}
        normalized_df = self.normalize_games()
        normalized_df = normalized_df.merge_with_teams(teams_df)
        # season wins/losses/ties/PF/PA for away teams, home teams
        away_df = pandas.pivot_table(
            normalized_df.convert_dtypes(),
            values=["a_win", "h_win", "a_tie", "a_score_norm", "h_score_norm"],
            index=a_index,
            aggfunc="sum",
            fill_value=0,
        )
        home_df = pandas.pivot_table(
            normalized_df.convert_dtypes(),
            values=["h_win", "a_win", "h_tie", "h_score_norm", "a_score_norm"],
            index=h_index,
            aggfunc="sum",
            fill_value=0,
        )

        # rename index and against columns
        away_df = away_df.rename(
            columns={"h_win": "a_loss", "h_score_norm": "a_score_norm_against"},
        ).rename_axis(index=a_rename)
        home_df = home_df.rename(
            columns={"a_win": "h_loss", "a_score_norm": "h_score_norm_against"},
        ).rename_axis(index=h_rename)
        # merge to one table. some teams will have only played away or home, so
        # fillna fills their other side with zeroes
        record_df = home_df.join(
            away_df,
            how="outer",
        ).fillna(0)
        # win total, loss total, game total, points for, points against, win percentage
        record_df["win_total"] = record_df["h_win"] + record_df["a_win"]
        record_df["loss_total"] = record_df["h_loss"] + record_df["a_loss"]
        record_df["tie_total"] = record_df["h_tie"] + record_df["a_tie"]
        record_df["games_played"] = (
            record_df["win_total"] + record_df["loss_total"] + record_df["tie_total"]
        )
        record_df["win_pct"] = (
            record_df["win_total"] + record_df["tie_total"] * 0.5
        ) / record_df["games_played"]
        record_df["points_for"] = record_df["h_score_norm"] + record_df["a_score_norm"]
        record_df["points_against"] = (
            record_df["h_score_norm_against"] + record_df["a_score_norm_against"]
        )
        record_df["avg_margin"] = (
            record_df["points_for"] - record_df["points_against"]
        ) / record_df["games_played"]
        record_df.sort_values(by="win_pct", ascending=False, inplace=True)
        record_df.drop(
            columns=[
                "h_win",
                "a_win",
                "h_loss",
                "a_loss",
                "h_tie",
                "a_tie",
                "h_score_norm",
                "a_score_norm",
                "h_score_norm_against",
                "a_score_norm_against",
            ],
            inplace=True,
        )
        return record_df

    def calc_matchup_records(self, teams_df):
        normalized_df = self.normalize_games()
        normalized_df = normalized_df.merge_with_teams(teams_df)
        # grouping for away and home matchup winners, ties, occurrences
        away_df = pandas.pivot_table(
            normalized_df,
            values=["a_win", "a_tie", "season"],
            index=["a_nick", "h_nick"],
            aggfunc={
                "a_win": "sum",
                "a_tie": "sum",
                "season": "count",
            },
            fill_value=0,
        ).rename(columns={"season": "a_games"})
        home_df = pandas.pivot_table(
            normalized_df,
            values=["h_win", "h_tie", "season"],
            index=["h_nick", "a_nick"],
            aggfunc={
                "h_win": "sum",
                "h_tie": "sum",
                "season": "count",
            },
            fill_value=0,
        ).rename(columns={"season": "h_games"})
        # rename indices
        away_df.index.set_names(names=["nick_name", "loser"], inplace=True)
        home_df.index.set_names(names=["nick_name", "loser"], inplace=True)
        # join and sum to get total matchup wins
        matchup_df = (
            away_df.join(
                home_df,
                how="outer",
            )
            .fillna(0)
            .convert_dtypes()
        )
        # ties count for 0.5
        matchup_df["win_total"] = (
            matchup_df["a_win"]
            + matchup_df["h_win"]
            + matchup_df["a_tie"] * 0.5
            + matchup_df["h_tie"] * 0.5
        )
        matchup_df["game_total"] = matchup_df["a_games"] + matchup_df["h_games"]
        # get rid of intermediate columns. just wins and games now
        matchup_df = matchup_df.convert_dtypes().drop(
            columns=[
                "a_win",
                "h_win",
                "a_tie",
                "h_tie",
                "a_games",
                "h_games",
            ]
        )
        # add win pct column and sort by
        matchup_df["win_pct"] = matchup_df["win_total"] / matchup_df["game_total"]
        matchup_df.sort_values(by=["win_pct"], ascending=False, inplace=True)
        return matchup_df


@ml_api.post("/team")
async def add_teams(
    doc_list: List[MLTeam],
    client: AsyncIOMotorClient = Depends(get_odm),
    user: UserOut = Depends(oauth2_scheme),
):
    engine = AIOEngine(motor_client=client, database="mildredleague")
    result = await engine.save_all(doc_list)
    # recalculate transforms
    transform_info = await transform_pipeline(client, run_all=True)
    return {
        "result": result,
        "transform_info": transform_info,
    }


@ml_api.get("/team/{oid}", response_model=MLTeam)
async def get_team(
    oid: ObjectId,
    client: AsyncIOMotorClient = Depends(get_odm),
):
    engine = AIOEngine(motor_client=client, database="mildredleague")
    team = await engine.find_one(MLTeam, MLTeam.id == oid)
    if team:
        return team
    else:
        raise HTTPException(status_code=404, detail="No data found!")


@ml_api.patch("/team/{oid}")
async def edit_team(
    oid: ObjectId,
    patch: MLTeamPatch,
    client: AsyncIOMotorClient = Depends(get_odm),
    user: UserOut = Depends(oauth2_scheme),
):
    engine = AIOEngine(motor_client=client, database="mildredleague")
    team = await engine.find_one(MLTeam, MLTeam.id == oid)
    if team is None:
        raise HTTPException(status_code=404, detail="No data found!")

    patch_dict = patch.dict(exclude_unset=True)
    for attr, value in patch_dict.items():
        setattr(team, attr, value)
    result = await engine.save(team)
    # recalculate transforms
    transform_info = await transform_pipeline(client, run_all=True)
    return {
        "result": result,
        "transform_info": transform_info,
    }


@ml_api.delete("/team/{oid}")
async def delete_team(
    oid: ObjectId,
    client: AsyncIOMotorClient = Depends(get_odm),
    user: UserOut = Depends(oauth2_scheme),
):
    engine = AIOEngine(motor_client=client, database="mildredleague")
    team = await engine.find_one(MLTeam, MLTeam.id == oid)
    if team is None:
        raise HTTPException(status_code=404, detail="No data found!")

    await engine.delete(team)
    # recalculate transforms
    transform_info = await transform_pipeline(client, run_all=True)
    return {
        "team": team,
        "transform_info": transform_info,
    }


@ml_api.get("/all/team/all", response_model=List[MLTeam])
async def get_all_teams(client: AsyncIOMotorClient = Depends(get_odm)):
    engine = AIOEngine(motor_client=client, database="mildredleague")
    # return full history of mildredleague teams
    data = [team async for team in engine.find(MLTeam, sort=MLTeam.id)]
    if data:
        return data
    else:
        raise HTTPException(status_code=404, detail="No data found!")


@ml_api.get("/{season}/team/all", response_model=List[MLTeam])
async def get_season_teams(
    season: MLSeason, client: AsyncIOMotorClient = Depends(get_odm)
):
    engine = AIOEngine(motor_client=client, database="mildredleague")
    data = [
        team
        async for team in engine.find(MLTeam, MLTeam.season == season, sort=MLTeam.id)
    ]
    if data:
        return data
    else:
        raise HTTPException(status_code=404, detail="No data found!")


@ml_api.post("/game")
async def add_games(
    doc_list: List[MLGame],
    client: AsyncIOMotorClient = Depends(get_odm),
    user: UserOut = Depends(oauth2_scheme),
):
    engine = AIOEngine(motor_client=client, database="mildredleague")
    result = await engine.save_all(doc_list)
    # recalculate transforms
    transform_info = await transform_pipeline(client, doc_list=doc_list)
    return {
        "result": result,
        "transform_info": transform_info,
    }


@ml_api.get("/game/{oid}", response_model=MLGame)
async def get_game(
    oid: ObjectId,
    client: AsyncIOMotorClient = Depends(get_odm),
):
    engine = AIOEngine(motor_client=client, database="mildredleague")
    game = await engine.find_one(MLGame, MLGame.id == oid)
    if game:
        return game
    else:
        raise HTTPException(status_code=404, detail="No data found!")


@ml_api.patch("/game/{oid}")
async def edit_game(
    oid: ObjectId,
    patch: MLGamePatch,
    client: AsyncIOMotorClient = Depends(get_odm),
    user: UserOut = Depends(oauth2_scheme),
):
    engine = AIOEngine(motor_client=client, database="mildredleague")
    game = await engine.find_one(MLGame, MLGame.id == oid)
    if game is None:
        raise HTTPException(status_code=404, detail="No data found!")

    patch_dict = patch.dict(exclude_unset=True)
    for attr, value in patch_dict.items():
        setattr(game, attr, value)
    result = await engine.save(game)
    # recalculate transforms
    transform_info = await transform_pipeline(client, doc_list=[game])
    return {
        "result": result,
        "transform_info": transform_info,
    }


@ml_api.delete("/game/{oid}")
async def delete_game(
    oid: ObjectId,
    client: AsyncIOMotorClient = Depends(get_odm),
    user: UserOut = Depends(oauth2_scheme),
):
    engine = AIOEngine(motor_client=client, database="mildredleague")
    game = await engine.find_one(MLGame, MLGame.id == oid)
    if game is None:
        raise HTTPException(status_code=404, detail="No data found!")

    await engine.delete(game)
    # recalculate transforms
    transform_info = await transform_pipeline(client, doc_list=[game])
    return {
        "game": game,
        "transform_info": transform_info,
    }


@ml_api.get("/all/game/all", response_model=List[MLGame])
async def get_all_games(client: AsyncIOMotorClient = Depends(get_odm)):
    engine = AIOEngine(motor_client=client, database="mildredleague")
    data = [
        game
        async for game in engine.find(
            MLGame,
            sort=MLGame.id,
        )
    ]
    if data:
        return data
    else:
        raise HTTPException(status_code=404, detail="No data found!")


@ml_api.get("/all/game/{playoff}", response_model=List[MLGame])
async def get_all_playoff_games(
    playoff: MLPlayoff, client: AsyncIOMotorClient = Depends(get_odm)
):
    engine = AIOEngine(motor_client=client, database="mildredleague")
    data = [
        game
        async for game in engine.find(
            MLGame,
            MLGame.playoff == playoff,
            sort=MLGame.id,
        )
    ]
    if data:
        return data
    else:
        raise HTTPException(status_code=404, detail="No data found!")


@ml_api.get("/{season}/game/all", response_model=List[MLGame])
async def get_season_games(
    season: MLSeason,
    client: AsyncIOMotorClient = Depends(get_odm),
):
    engine = AIOEngine(motor_client=client, database="mildredleague")
    data = [
        game
        async for game in engine.find(
            MLGame,
            MLGame.season == season,
            sort=MLGame.id,
        )
    ]
    if data:
        return data
    else:
        raise HTTPException(status_code=404, detail="No data found!")


@ml_api.get("/{season}/game/{playoff}", response_model=List[MLGame])
async def get_season_games_subset(
    season: MLSeason,
    playoff: MLPlayoff,
    client: AsyncIOMotorClient = Depends(get_odm),
):
    engine = AIOEngine(motor_client=client, database="mildredleague")
    data = [
        game
        async for game in engine.find(
            MLGame,
            (MLGame.season == season) & (MLGame.playoff == playoff),
            sort=MLGame.id,
        )
    ]
    if data:
        return data
    else:
        raise HTTPException(status_code=404, detail="No data found!")


@ml_api.post("/note")
async def add_notes(
    doc_list: List[MLNote],
    client: AsyncIOMotorClient = Depends(get_odm),
    user: UserOut = Depends(oauth2_scheme),
):
    engine = AIOEngine(motor_client=client, database="mildredleague")
    result = await engine.save_all(doc_list)
    return {
        "result": result,
    }


@ml_api.get("/note/{oid}", response_model=MLNote)
async def get_note(
    oid: ObjectId,
    client: AsyncIOMotorClient = Depends(get_odm),
):
    engine = AIOEngine(motor_client=client, database="mildredleague")
    note = await engine.find_one(MLNote, MLNote.id == oid)
    if note:
        return note
    else:
        raise HTTPException(status_code=404, detail="No data found!")


@ml_api.patch("/note/{oid}")
async def edit_note(
    oid: ObjectId,
    patch: MLNotePatch,
    client: AsyncIOMotorClient = Depends(get_odm),
    user: UserOut = Depends(oauth2_scheme),
):
    engine = AIOEngine(motor_client=client, database="mildredleague")
    note = await engine.find_one(MLNote, MLNote.id == oid)
    if note is None:
        raise HTTPException(status_code=404, detail="No data found!")

    patch_dict = patch.dict(exclude_unset=True)
    for attr, value in patch_dict.items():
        setattr(note, attr, value)
    result = await engine.save(note)

    return {
        "result": result,
    }


@ml_api.delete("/note/{oid}")
async def delete_note(
    oid: ObjectId,
    client: AsyncIOMotorClient = Depends(get_odm),
    user: UserOut = Depends(oauth2_scheme),
):
    engine = AIOEngine(motor_client=client, database="mildredleague")
    note = await engine.find_one(MLNote, MLNote.id == oid)
    if note is None:
        raise HTTPException(status_code=404, detail="No data found!")

    await engine.delete(note)

    return {
        "note": note,
    }


@ml_api.get("/all/note/all", response_model=List[MLNote])
async def get_season_notes(
    client: AsyncIOMotorClient = Depends(get_odm),
):
    engine = AIOEngine(motor_client=client, database="mildredleague")
    data = [
        note
        async for note in engine.find(MLNote, sort=MLNote.id)
    ]
    if data:
        return data
    else:
        raise HTTPException(status_code=404, detail="No data found!")


@ml_api.get("/{season}/note/all", response_model=List[MLNote])
async def get_season_notes(
    season: MLSeason,
    client: AsyncIOMotorClient = Depends(get_odm),
):
    engine = AIOEngine(motor_client=client, database="mildredleague")
    data = [
        note
        async for note in engine.find(MLNote, MLNote.season == season, sort=MLNote.id)
    ]
    if data:
        return data
    else:
        raise HTTPException(status_code=404, detail="No data found!")


@ml_api.get("/all/figure/ranking")
async def all_time_ranking_fig(teams_data: List[MLTeam] = Depends(get_all_teams)):
    # convert to pandas dataframe
    teams_df = pandas.DataFrame([team.doc() for team in teams_data])
    # pivot by year for all teams
    annual_ranking_df = pandas.pivot(
        teams_df, index="nick_name", columns="season", values="playoff_rank"
    )

    # temporary variable to rank relevance of a team.
    # higher numbers are less relevant.
    # 15 for teams that didn't play in a given year
    # (worst rank for a team that existed would be 14)
    annual_ranking_df_temp = annual_ranking_df.fillna(15)
    annual_ranking_df_temp["relevance"] = annual_ranking_df_temp.sum(axis=1)
    annual_ranking_df["relevance"] = annual_ranking_df_temp["relevance"]
    annual_ranking_df.sort_values(by="relevance", ascending=False, inplace=True)
    annual_ranking_df.reset_index(inplace=True)

    # y axis labels
    y_ranking_names = annual_ranking_df.nick_name.to_list()

    # drop unnecessary columns
    annual_ranking_df.drop(columns=["nick_name", "relevance"], inplace=True)

    # x axis labels
    x_seasons = annual_ranking_df.columns.tolist()

    # need to pull out of data frame format for this particular figure,
    # and replace np.nan with 0 (to then replace with None)
    z_rankings = annual_ranking_df.fillna(0).values.tolist()

    heatmap_colors = [
        [i / (len(plotly.colors.diverging.Temps) - 1), color]
        for i, color in enumerate(plotly.colors.diverging.Temps)
    ]

    return {
        "x_seasons": x_seasons,
        "y_ranking_names": y_ranking_names,
        "z_rankings": z_rankings,
        "heatmap_colors": heatmap_colors,
    }


@ml_api.get("/all/figure/wins/{playoff}")
async def win_total_fig(
    playoff: MLPlayoff,
    games_data: List[MLGame] = Depends(get_all_playoff_games),
    teams_data: List[MLTeam] = Depends(get_all_teams),
):
    # convert to pandas DataFrame and normalize as record_df
    games_df = MLTable([game.doc() for game in games_data])
    teams_df = pandas.DataFrame([team.doc() for team in teams_data])
    record_df = games_df.calc_records(teams_df, divisions=False)
    # group by nick_name (don't need division info for this figure)
    record_df = (
        record_df.groupby(
            level=["nick_name"],
        )
        .agg({"win_total": sum})
        .sort_values("win_total", ascending=True)
    )

    # create list of x_data and y_data
    x_data = [int(data_point) for data_point in list(record_df.win_total.values)]
    y_data = record_df.index.tolist()
    # color data needs to be tripled to have enough
    # colors for every bar!
    color_data = (
        px.colors.cyclical.Phase[1:]
        + px.colors.cyclical.Phase[1:]
        + px.colors.cyclical.Phase[1:]
    )

    return {
        "x_data": x_data,
        "y_data": y_data,
        "color_data": color_data,
    }


@ml_api.get("/all/figure/heatmap")
async def matchup_heatmap_fig(
    games_data: List[MLGame] = Depends(get_all_games),
    teams_data: List[MLTeam] = Depends(get_all_teams),
):
    # convert to pandas DataFrame
    games_df = MLTable([game.doc() for game in games_data])
    teams_df = pandas.DataFrame([team.doc() for team in teams_data])
    # convert to record_df
    matchup_df = games_df.calc_matchup_records(teams_df.copy()).reset_index()

    # inner joins are just to keep active teams
    active_matchup_df = (
        matchup_df.merge(
            teams_df.loc[teams_df.active, ["nick_name"]].drop_duplicates(),
            on="nick_name",
            how="inner",
        )
        .merge(
            teams_df.loc[teams_df.active, ["nick_name"]].drop_duplicates(),
            left_on="loser",
            right_on="nick_name",
            how="inner",
        )
        .drop(columns=["nick_name_y"])
        .rename(columns={"nick_name_x": "nick_name"})
        .set_index(keys=["nick_name", "loser"])
    )

    # game total custom data for the hover text
    game_df = active_matchup_df[["game_total"]].unstack()
    # win pct data is what drives the figure
    matchup_df = active_matchup_df[["win_pct"]].unstack()

    # start creating the figure!
    # y axis labels
    y_winners = matchup_df.index.to_list()
    y_winners.reverse()
    # x axis labels
    x_opponents = matchup_df.columns.get_level_values(1).to_list()
    # z axis data, replacing nan with 0s
    z_matchup_data = matchup_df[["win_pct"]].fillna(-1).values.tolist()
    z_matchup_data.reverse()
    # custom hovertext data, replacing nan with 0s
    hover_data = game_df[["game_total"]].fillna(0).values.tolist()
    hover_data.reverse()
    # color data
    matchup_colors = [
        [i / (len(plotly.colors.diverging.Temps_r) - 1), color]
        for i, color in enumerate(plotly.colors.diverging.Temps_r)
    ]

    return {
        "x_opponents": x_opponents,
        "y_winners": y_winners,
        "z_matchup_data": z_matchup_data,
        "matchup_colors": matchup_colors,
        "hover_data": hover_data,
    }


@ml_api.get("/{season}/boxplot", response_model=MLBoxplotTransform)
async def season_boxplot_fig(
    season: MLSeason,
    client: AsyncIOMotorClient = Depends(get_odm),
):
    engine = AIOEngine(motor_client=client, database="mildredleague")
    chart_data = [
        chart
        async for chart in engine.find(
            MLBoxplotTransform,
            MLBoxplotTransform.season == season,
        )
    ]
    # if no chart data is found, rerun pipeline for all cached charts,
    # then query again
    if not chart_data:
        await transform_pipeline(client, run_all=True)
        chart_data = [
            chart
            async for chart in engine.find(
                MLBoxplotTransform,
                MLBoxplotTransform.season == season,
            )
        ]
    return chart_data[0]


@ml_api.get("/{season}/table/{playoff}", response_model=MLTableTransform)
async def season_table(
    season: MLSeason,
    playoff: MLPlayoff,
    client: AsyncIOMotorClient = Depends(get_odm),
):
    engine = AIOEngine(motor_client=client, database="mildredleague")
    table_data = [
        table
        async for table in engine.find(
            MLTableTransform,
            MLTableTransform.season == season,
            MLTableTransform.playoff == playoff,
        )
    ]
    if not table_data:
        await transform_pipeline(client, run_all=True)
        table_data = [
            table
            async for table in engine.find(
                MLTableTransform,
                MLTableTransform.season == season,
                MLTableTransform.playoff == playoff,
            )
        ]
    return table_data[0]


async def transform_pipeline(client: AsyncIOMotorClient, doc_list=None, run_all=False):
    # set up data arrays
    season_games_data_array = []
    season_teams_data_array = []
    season_games_subset_data_array = []
    boxplot_message_array = []
    ranking_message_array = []

    if doc_list:
        season_playoff_combos = list(
            set([(doc.dict()["season"], doc.dict()["playoff"]) for doc in doc_list])
        )
    elif run_all:
        all_seasons = [member for name, member in MLSeason.__members__.items()]
        all_playoffs = [member for name, member in MLPlayoff.__members__.items()]
        season_playoff_combos = list(product(all_seasons, all_playoffs))
    else:
        raise Exception("Something weird happened with the pipeline...")

    for combo in season_playoff_combos:
        season_games_data_array.append(await get_season_games(combo[0], client))
        season_teams_data_array.append(await get_season_teams(combo[0], client))
        season_games_subset_data_array.append(
            await get_season_games_subset(combo[0], combo[1], client)
        )

    for i, dataset in enumerate(season_teams_data_array):
        boxplot_message = await season_boxplot_transform(
            season_playoff_combos[i][0],
            season_games_data_array[i],
            season_teams_data_array[i],
            client,
        )
        boxplot_message_array.append(boxplot_message)

        ranking_message = await season_table_transform(
            season_playoff_combos[i][0],
            season_playoff_combos[i][1],
            season_games_subset_data_array[i],
            season_teams_data_array[i],
            client,
        )
        ranking_message_array.append(ranking_message)

    return {
        "boxplot_message": boxplot_message_array,
        "ranking_message": ranking_message_array,
    }


async def season_boxplot_transform(
    season: MLSeason,
    season_games_data: List[MLGame],
    season_teams_data: List[MLTeam],
    client: AsyncIOMotorClient,
):
    # convert to DataFrame
    season_df = pandas.DataFrame([game.doc() for game in season_games_data])
    # normalized score columns for two-week playoff games
    season_df["a_score_norm"] = season_df["a_score"] / (
        season_df["week_e"] - season_df["week_s"] + 1
    )
    season_df["h_score_norm"] = season_df["h_score"] / (
        season_df["week_e"] - season_df["week_s"] + 1
    )
    # we just want unique scores. so let's stack away and home.
    # this code runs to analyze Points For.
    score_df_for = (
        season_df[["a_nick", "a_score_norm"]]
        .rename(
            columns={"a_nick": "name", "a_score_norm": "score"},
        )
        .append(
            season_df[["h_nick", "h_score_norm"]].rename(
                columns={"h_nick": "name", "h_score_norm": "score"},
            ),
            ignore_index=True,
        )
    )
    score_df_for["side"] = "for"
    # this code runs to analyze Points Against.
    score_df_against = (
        season_df[["a_nick", "h_score_norm"]]
        .rename(
            columns={"a_nick": "name", "h_score_norm": "score"},
        )
        .append(
            season_df[["h_nick", "a_score_norm"]].rename(
                columns={"h_nick": "name", "a_score_norm": "score"},
            ),
            ignore_index=True,
        )
    )
    score_df_against["side"] = "against"
    score_df = pandas.concat([score_df_for, score_df_against])
    # let's sort by playoff rank instead
    # read season file, but we only need nick_name, season, and playoff_rank
    ranking_df = pandas.DataFrame([team.doc() for team in season_teams_data])[["nick_name", "playoff_rank"]]
    # merge this (filtered by season) into score_df so we can sort values
    score_df = score_df.merge(
        ranking_df,
        left_on=["name"],
        right_on=["nick_name"],
        how="left",
    ).sort_values(
        by="playoff_rank",
        ascending=True,
    )

    # filter out Bye games
    score_df = score_df.loc[score_df.name != "Bye"]

    # for and against split
    score_df_for = score_df.loc[score_df.side == "for"]
    score_df_against = score_df.loc[score_df.side == "against"]

    # names on the X axis
    x_data_for = score_df_for.nick_name.unique().tolist()
    x_data_against = score_df_against.nick_name.unique().tolist()

    # Y axis is scores. need 2D array
    y_data_for = [
        score_df_for.loc[score_df_for.nick_name == name, "score"].tolist()
        for name in x_data_for
    ]
    y_data_against = [
        score_df_against.loc[score_df_against.nick_name == name, "score"].tolist()
        for name in x_data_against
    ]

    # list of hex color codes
    color_data = px.colors.qualitative.Light24

    # convert to json for writing to Mongo
    new_chart_data = MLBoxplotTransform(
        season=season,
        for_data={
            "x_data": x_data_for,
            "y_data": y_data_for,
            "color_data": color_data,
        },
        against_data={
            "x_data": x_data_against,
            "y_data": y_data_against,
            "color_data": color_data,
        },
    )

    # write data to MongoDB
    engine = AIOEngine(motor_client=client, database="mildredleague")
    old_chart_data = [
        chart
        async for chart in engine.find(
            MLBoxplotTransform,
            MLBoxplotTransform.season == season,
        )
    ]
    if old_chart_data == [new_chart_data]:
        message = (
            "Collection is already synced! Collection: " + str(new_chart_data.season)
        )
    else:
        # if boxplots need to be recalculated, just wipe the collection and reinsert
        for chart in old_chart_data:
            await engine.delete(chart)
        await engine.save(new_chart_data)
        message = (
            "Bulk delete and insert complete! Collection: " + str(new_chart_data.season)
        )

    return message


async def season_table_transform(
    season: MLSeason,
    playoff: MLPlayoff,
    season_games_subset_data: List[MLGame],
    season_teams_data: List[MLTeam],
    client: AsyncIOMotorClient,
):
    # convert to pandas DataFrame and normalize
    games_df = MLTable([game.doc() for game in season_games_subset_data])
    teams_df = pandas.DataFrame([team.doc() for team in season_teams_data]).set_index("_id")
    if playoff > 0:
        if playoff == 2:
            # for loser's bracket, sort by games played ascending first,
            # so teams from winner's bracket end up at the top. then sort by
            # win total descending and points for descending
            by_list = ["playoff_rank", "games_played", "win_total", "points_for"]
            ascend_list = [True, True, False, False]
        else:
            # for winner's bracket, sort by games played descending first,
            # so teams staying alive longer end up at the top. then sort
            # by win_pct descending.
            by_list = ["playoff_rank", "games_played", "win_pct"]
            ascend_list = [True, False, False]
        # run calc records for the playoff season
        season_table = games_df.calc_records(teams_df.copy())
        # merge playoff ranking
        season_table = (
            season_table.merge(
                teams_df[["division", "nick_name", "playoff_rank"]],
                left_index=True,
                right_on=["division", "nick_name"],
                how="left",
            )
            .sort_values(
                by=by_list,
                ascending=ascend_list,
            )
            .set_index(["division", "nick_name"])
            .reset_index()
        )
        new_table_data = json.loads(season_table.to_json(orient="split", index=False))
    else:
        # to resolve tiebreakers, need records for the season
        season_records_df = games_df.calc_records(teams_df.copy())
        # also bring in H2H matchup records
        matchup_df = games_df.calc_matchup_records(teams_df.copy())

        # initial division ranking before tiebreakers.
        season_records_df["division_rank"] = season_records_df.groupby(
            level=["division"],
        )["win_pct"].rank(
            method="min",
            ascending=False,
        )

        # begin loop to resolve division ties.
        for div in season_records_df.index.unique(level="division"):
            # filter down to the division of interest.
            div_df = season_records_df.loc[[div]]
            # let's calculate division record here
            div_matchups = list(
                permutations(div_df.index.get_level_values("nick_name"), 2)
            )
            # group by winner to determine H2H among the group
            div_matchup_df = (
                matchup_df.loc[div_matchups]
                .groupby(level="nick_name")
                .agg({"win_total": sum, "game_total": sum})
            )
            # win_pct in the divisional grouping, then join back to div_df
            div_matchup_df["win_pct_div"] = (
                div_matchup_df["win_total"] / div_matchup_df["game_total"]
            )
            div_df = div_df.join(div_matchup_df[["win_pct_div"]])
            # loop over division_rank to determine where ties need to be broken.
            for rank in div_df.division_rank.unique():
                # if the length of the df is longer than 1 for any rank, there's a tie...
                tied_df = div_df.loc[div_df.division_rank == rank]
                if len(tied_df) > 1:
                    untied_df = division_tiebreaker_one(tied_df, matchup_df)
                    div_df.update(untied_df)
            season_records_df.update(div_df)

        # begin to determine playoff seed. first, separate the three division winners.
        div_winners_df = season_records_df.loc[season_records_df.division_rank == 1]
        div_losers_df = season_records_df.loc[season_records_df.division_rank > 1]
        # calculate initial seeding based on pure win_pct.
        div_winners_df["playoff_seed"] = div_winners_df.win_pct.rank(
            method="min",
            ascending=False,
        )
        div_losers_df["playoff_seed"] = (
            div_losers_df.win_pct.rank(
                method="min",
                ascending=False,
            )
            + len(div_winners_df)
        )

        # now, tiebreakers...winners first
        for seed in range(1, len(div_winners_df)):
            # if the length of the df is longer than 1 for any rank, there's a tie...
            tied_df = div_winners_df.loc[div_winners_df.playoff_seed == seed]
            if len(tied_df) > 1:
                untied_df = wild_card_tiebreaker_one(tied_df, games_df, matchup_df)
                div_winners_df.update(untied_df)

        # break the rest of the ties for division losers.
        for seed in range(len(div_winners_df) + 1, len(season_records_df)):
            # if the length of the df is longer than 1 for any rank, there's a tie...
            tied_df = div_losers_df.loc[div_losers_df.playoff_seed == seed]
            if len(tied_df) > 1:
                untied_df = wild_card_tiebreaker_one(tied_df, games_df, matchup_df)
                div_losers_df.update(untied_df)

        season_table = pandas.concat([div_winners_df, div_losers_df]).sort_values(
            by="playoff_seed"
        )

        new_table_data = json.loads(
            season_table.reset_index().to_json(orient="split", index=False)
        )

    # set missing elements in table data for mongo
    new_table_data = MLTableTransform(
        season=season,
        playoff=playoff,
        columns=new_table_data['columns'],
        data=new_table_data['data'],
    )

    # write data to MongoDB
    engine = AIOEngine(motor_client=client, database="mildredleague")
    old_table_data = [
        table
        async for table in engine.find(
            MLTableTransform,
            MLTableTransform.season == season,
            MLTableTransform.playoff == playoff,
        )
    ]
    if old_table_data == [new_table_data]:
        message = (
            "Collection is already synced! Collection: " + str(new_table_data.season) + str(new_table_data.playoff)
        )
    else:
        # if tables need to be recalculated, just wipe the collection and reinsert
        for table in old_table_data:
            await engine.delete(table)
        await engine.save(new_table_data)
        message = (
            "Bulk delete and insert complete! Collection: " + str(new_table_data.season) + str(new_table_data.playoff)
        )

    return message


@ml_api.get("/{season}/sim")
async def seed_sim(
    season: MLSeason,
    games_data: List[MLGame] = Depends(get_season_games),
    winners_array=["t1", "t2", "t3", "t4", "t5", "t6", "t7"],
):
    # this function will need to be reimplemented next year!
    # return garbage for now.
    return winners_array
    # convert to dataframe
    games_df = pandas.DataFrame(games_data).set_index("_id")

    # we're going to concatenate the API data with simulated data
    # that the user has chosen, so we can rerun tiebreakers
    sim_df = pandas.DataFrame(
        data=[
            [
                "Division 6",
                "Referees",
                "AFC East",
                "Division 6",
                "Referees",
                "AFC East",
                "Referees",
            ],
            ["sim" for i in range(0, 7)],
            [
                "Tarpey",
                "Charles",
                "Conti",
                "Frank",
                "mballen",
                "Jake",
                "Brad",
            ],
            [
                winners_array.count("Tarpey") * 20 + 80,
                winners_array.count("Charles") * 20 + 80,
                winners_array.count("Conti") * 20 + 80,
                winners_array.count("Frank") * 20 + 80,
                winners_array.count("mballen") * 20 + 80,
                winners_array.count("Jake") * 20 + 80,
                winners_array.count("Brad") * 20 + 80,
            ],
            ["sim" for i in range(0, 7)],
            [
                "Division 6",
                "Referees",
                "AFC East",
                "Division 6",
                "AFC East",
                "AFC East",
                "Referees",
            ],
            ["sim" for i in range(0, 7)],
            [
                "Brando",
                "Mildred",
                "Samik",
                "Fonti",
                "Sendzik",
                "Kindy",
                "Tommy",
            ],
            [
                winners_array.count("Brando") * 20 + 80,
                winners_array.count("Mildred") * 20 + 80,
                winners_array.count("Samik") * 20 + 80,
                winners_array.count("Fonti") * 20 + 80,
                winners_array.count("Sendzik") * 20 + 80,
                winners_array.count("Kindy") * 20 + 80,
                winners_array.count("Tommy") * 20 + 80,
            ],
            ["sim" for i in range(0, 7)],
            [0 for i in range(0, 7)],
            [2020 for i in range(0, 7)],
            [14 for i in range(0, 7)],
            [14 for i in range(0, 7)],
        ]
    ).transpose()
    sim_df.columns = games_df.columns.tolist()
    sim_df = pandas.concat([games_df, sim_df], ignore_index=True)

    # table = season_table_active(season, sim_df)[[
    #     'division',
    #     'nick_name',
    #     'win_total',
    #     'loss_total',
    #     'tie_total',
    #     'division_rank',
    #     'playoff_seed',
    # ]]

    return None


def division_tiebreaker_one(tied_df, matchup_df):
    # figure out who's got H2H among the 2+ teams by generating all possible matchups
    matchups = list(permutations(tied_df.index.get_level_values("nick_name"), 2))
    # group by winner to determine H2H among the group
    matchup_df = (
        matchup_df.loc[matchups]
        .groupby(level="nick_name")
        .agg({"win_total": sum, "game_total": sum})
    )
    # win_pct in this H2H grouping
    matchup_df["win_pct_h2h"] = matchup_df["win_total"] / matchup_df["game_total"]
    matchup_df["tiebreaker_rank"] = (
        matchup_df.win_pct_h2h.rank(
            method="min",
            ascending=False,
        )
        - 1
    )

    # recalculate div rank now
    tied_df = tied_df.join(matchup_df[["tiebreaker_rank"]])
    tied_df["division_rank"] = tied_df["division_rank"] + tied_df["tiebreaker_rank"]

    # check time! are we still tied or is it broken?
    for rank in tied_df.division_rank.unique():
        # if the length of the df is longer than 1 for any rank, there's a tie...
        # proceed to tiebreaker #2, which is division record.
        still_tied_df = tied_df.loc[tied_df.division_rank == rank]
        if len(still_tied_df) > 1:
            untied_df = division_tiebreaker_two(still_tied_df)
            tied_df.update(untied_df)

    return tied_df


def division_tiebreaker_two(tied_df):
    # rank based on win_pct_div
    tied_df["tiebreaker_two_rank"] = (
        tied_df.win_pct_div.rank(
            method="min",
            ascending=False,
        )
        - 1
    )

    # recalculate div rank now
    tied_df["division_rank"] = tied_df["division_rank"] + tied_df["tiebreaker_two_rank"]

    # check time! are we still tied or is it broken?
    for rank in tied_df.division_rank.unique():
        # if the length of the df is longer than 1 for any rank, there's a tie...
        # proceed to tiebreaker #3, which is points for.
        still_tied_df = tied_df.loc[tied_df.division_rank == rank]
        if len(still_tied_df) > 1:
            untied_df = division_tiebreaker_three(still_tied_df)
            tied_df.update(untied_df)

    return tied_df


def division_tiebreaker_three(tied_df):
    # rank based on points for
    tied_df["tiebreaker_three_rank"] = (
        tied_df.points_for.rank(
            method="min",
            ascending=False,
        )
        - 1
    )

    # recalculate div rank now
    tied_df["division_rank"] = (
        tied_df["division_rank"] + tied_df["tiebreaker_three_rank"]
    )

    # check time! are we still tied or is it broken?
    for rank in tied_df.division_rank.unique():
        # if the length of the df is longer than 1 for any rank, there's a tie...
        # proceed to tiebreaker #4, which is points against
        still_tied_df = tied_df.loc[tied_df.division_rank == rank]
        if len(still_tied_df) > 1:
            untied_df = division_tiebreaker_four(still_tied_df)
            tied_df.update(untied_df)

    return tied_df


def division_tiebreaker_four(tied_df):
    # rank based on points against
    tied_df["tiebreaker_four_rank"] = (
        tied_df.points_against.rank(
            method="min",
            ascending=False,
        )
        - 1
    )

    # recalculate div rank now
    tied_df["division_rank"] = (
        tied_df["division_rank"] + tied_df["tiebreaker_four_rank"]
    )

    # check time! are we still tied or is it broken?
    for rank in tied_df.division_rank.unique():
        # if the length of the df is longer than 1 for any rank, there's a tie...
        # proceed to tiebreaker #5, which is a real life coin flip.
        still_tied_df = tied_df.loc[tied_df.division_rank == rank]
        if len(still_tied_df) > 1:
            print(still_tied_df)
            print("You're gonna need a coin for this one.")

    return tied_df


def wild_card_tiebreaker_one(tied_df, games_df, matchup_df):
    # need to filter out any teams at this stage that aren't the highest-ranked
    # team in their division in the tiebreaker.
    seed_to_break = tied_df.playoff_seed.min()
    # if this tiebreaker only involves one division, just use division ranking
    if len(tied_df.index.unique(level="division")) == 1:
        tied_df["playoff_seed"] = (
            tied_df.division_rank.rank(
                method="min",
                ascending=True,
            )
            + seed_to_break
            - 1
        )
    else:
        # with two or more divisions involved, it's on to H2H record.
        # but we can only compare the top remaining team in each division.
        # here we need to filter any team that doesn't meet that criteria
        # and add one to their playoff seed, so they'll be included
        # in the next tiebreaker sequence.
        # let's do a groupby object to get the min division rank in each
        # division.
        filter_df = (
            tied_df.groupby("division")
            .agg({"division_rank": min})
            .rename(columns={"division_rank": "qualifying_rank"})
        )
        # if we're looping back through here after a qualifying rank was
        # determined in an earlier tiebreak for the same seed, this join will blow up
        # (we don't need to recalculate the qualifying rank until looking
        # at the next seed). so check for qualifying rank here before joining
        if "qualifying_rank" not in tied_df.columns:
            tied_df = tied_df.join(filter_df)
        # split the tied_df here between teams that qualify to continue
        # the tiebreaker and teams that have to wait for the next seed
        qualified_tied_df = tied_df.loc[
            tied_df.division_rank == tied_df.qualifying_rank
        ]
        disqualified_tied_df = tied_df.loc[
            tied_df.division_rank != tied_df.qualifying_rank
        ]

        # send qualified teams to the next tiebreaker. when they return, concat
        # with the disqualified teams
        untied_df = wild_card_tiebreaker_two(
            qualified_tied_df, games_df, matchup_df, seed_to_break
        )

        # for wild card seeds, only one team can advance at a time.
        # the rest of the remaining teams have to be reconsidered in the next
        # seed's tiebreaker, so we reset seeds that weren't really tiebroken here.
        disqualified_tied_df["playoff_seed"] = seed_to_break + 1

        # concat happens here inside the update
        tied_df.update(pandas.concat([untied_df, disqualified_tied_df]))

    return tied_df


def wild_card_tiebreaker_two(tied_df, games_df, matchup_df, seed_to_break):
    # figure out who's got H2H among the 2-3 teams by generating all possible matchups
    matchups = list(permutations(tied_df.index.get_level_values("nick_name"), 2))
    # group by winner to determine H2H among the group
    wc_matchup_df = (
        matchup_df.loc[matchup_df.index.intersection(matchups)]
        .groupby(level="nick_name")
        .agg({"win_total": sum, "game_total": sum})
    )
    # win_pct in this H2H grouping
    wc_matchup_df["win_pct_h2h"] = (
        wc_matchup_df["win_total"] / wc_matchup_df["game_total"]
    )

    # our sweep check will just be whether or not game_total in a row is
    # 1 (in case of a 2-way tie) or 2 (in case of a 3-way tie). If it's not,
    # H2H will be skipped for that team (set win_pct_h2h to .500)
    wc_matchup_df.loc[
        wc_matchup_df.game_total < len(wc_matchup_df) - 1, "win_pct_h2h"
    ] = 0.5

    # now determine H2H rank in the group
    wc_matchup_df["wc_tiebreaker_two_rank"] = (
        wc_matchup_df.win_pct_h2h.rank(
            method="min",
            ascending=False,
        )
        - 1
    )

    # if we're looping back through here after a tiebreaker rank was
    # determined in an earlier tiebreak for the same seed, this join will blow up
    # so check for tiebreaker rank here before joining. if the column
    # is already there, just update it.
    if "wc_tiebreaker_two_rank" not in tied_df.columns:
        tied_df = tied_df.join(wc_matchup_df[["wc_tiebreaker_two_rank"]])
    else:
        tied_df.update(wc_matchup_df[["wc_tiebreaker_two_rank"]])

    # if this is a two way tiebreaker where there was no H2H,
    # we'll have to fill in tiebreaker_two with zeroes
    # before we modify the playoff seed
    tied_df["wc_tiebreaker_two_rank"] = tied_df["wc_tiebreaker_two_rank"].fillna(0)

    # now modify playoff seed
    tied_df["playoff_seed"] = (
        tied_df["playoff_seed"] + tied_df["wc_tiebreaker_two_rank"]
    )

    # for wild card seeds, only one team can advance at a time.
    # the rest of the remaining teams have to be reconsidered in the next
    # seed's tiebreaker, so we reset seeds that weren't really tiebroken here.
    tied_df.loc[tied_df.playoff_seed != seed_to_break, "playoff_seed"] = (
        seed_to_break + 1
    )

    # check time! are we still tied or is it broken?
    # if the count of teams at the seed_to_break is the same as before,
    # proceed to tiebreaker #3, which is points for.
    still_tied_df = tied_df.loc[tied_df.playoff_seed == seed_to_break]
    disqualified_tied_df = tied_df.loc[tied_df.playoff_seed > seed_to_break]
    if len(still_tied_df) == len(tied_df):
        untied_df = wild_card_tiebreaker_three(still_tied_df, seed_to_break)
        tied_df.update(untied_df)
    # there's also the case where someone has dropped out of the tiebreaker;
    # here we need to restart from step one with just the remaining teams.
    elif len(still_tied_df) > 1:
        untied_df = wild_card_tiebreaker_one(still_tied_df, games_df, matchup_df)
        tied_df.update(pandas.concat([untied_df, disqualified_tied_df]))

    return tied_df


def wild_card_tiebreaker_three(tied_df, seed_to_break):
    # rank based on points for
    tied_df["wc_tiebreaker_three_rank"] = (
        tied_df.points_for.rank(
            method="min",
            ascending=False,
        )
        - 1
    )

    # recalculate playoff seed now
    tied_df["playoff_seed"] = (
        tied_df["playoff_seed"] + tied_df["wc_tiebreaker_three_rank"]
    )

    # for wild card seeds, only one team can advance at a time.
    # the rest of the remaining teams have to be reconsidered in the next
    # seed's tiebreaker, so we reset seeds that weren't really tiebroken here.
    tied_df.loc[tied_df.playoff_seed != seed_to_break, "playoff_seed"] = (
        seed_to_break + 1
    )

    # check time! are we still tied or is it broken?
    # if the count of teams at the seed_to_break is the same as before,
    # proceed to tiebreaker #4, which is points against.
    still_tied_df = tied_df.loc[tied_df.playoff_seed == seed_to_break]
    disqualified_tied_df = tied_df.loc[tied_df.playoff_seed > seed_to_break]
    if len(still_tied_df) == len(tied_df):
        untied_df = wild_card_tiebreaker_four(still_tied_df, seed_to_break)
        tied_df.update(untied_df)
    # there's also the case where someone has dropped out of the tiebreaker;
    # here we need to restart from step one with just the remaining teams.
    elif len(still_tied_df) > 1:
        untied_df = wild_card_tiebreaker_one(still_tied_df)
        tied_df.update(pandas.concat([untied_df, disqualified_tied_df]))

    return tied_df


def wild_card_tiebreaker_four(tied_df, seed_to_break):
    # rank based on points against
    tied_df["wc_tiebreaker_four_rank"] = (
        tied_df.points_against.rank(
            method="min",
            ascending=False,
        )
        - 1
    )

    # recalculate playoff seed now
    tied_df["playoff_seed"] = (
        tied_df["playoff_seed"] + tied_df["wc_tiebreaker_four_rank"]
    )

    # for wild card seeds, only one team can advance at a time.
    # the rest of the remaining teams have to be reconsidered in the next
    # seed's tiebreaker, so we reset seeds that weren't really tiebroken here.
    tied_df.loc[tied_df.playoff_seed != seed_to_break, "playoff_seed"] = (
        seed_to_break + 1
    )

    # check time! are we still tied or is it broken?
    # if the count of teams at the seed_to_break is the same as before,
    # proceed to tiebreaker #5, which is an irl coin flip.
    still_tied_df = tied_df.loc[tied_df.playoff_seed == seed_to_break]
    disqualified_tied_df = tied_df.loc[tied_df.playoff_seed > seed_to_break]
    if len(still_tied_df) == len(tied_df):
        print(still_tied_df)
        print("You're gonna need a coin for this one. Or maybe a six-sided die.")
    # there's also the case where someone has dropped out of the tiebreaker;
    # here we need to restart from step one with just the remaining teams.
    elif len(still_tied_df) > 1:
        untied_df = wild_card_tiebreaker_one(still_tied_df)
        tied_df.update(pandas.concat([untied_df, disqualified_tied_df]))

    return tied_df
