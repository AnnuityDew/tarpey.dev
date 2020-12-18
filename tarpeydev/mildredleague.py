# import native Python packages
from itertools import permutations
import json

# import third party packages
from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates


# import custom local stuff
from api.mildredleague import (
    MLGame, MLTeam, MLNote, get_all_teams, get_all_games, get_season_games
)


# router and templates
ml_views = APIRouter(prefix="/mildredleague")
templates = Jinja2Templates(directory='templates')


@ml_views.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse(
        'mildredleague/home.html',
        context={'request': request},
    )


@ml_views.get("/add-game", response_class=HTMLResponse)
def add_game(request: Request):
    return templates.TemplateResponse(
        'mildredleague/add.html',
        context={'request': request},
    )


@ml_views.get("/edit-game", response_class=HTMLResponse)
def edit_game(request: Request):
    return templates.TemplateResponse(
        'mildredleague/edit.html',
        context={'request': request},
    )


@ml_views.get("/add-note", response_class=HTMLResponse)
def add_note(request: Request):
    return templates.TemplateResponse(
        'mildredleague/notes.html',
        context={'request': request},
    )


@ml_views.get("/all-time", response_class=HTMLResponse)
def all_time(request: Request, teams_data: MLTeam = Depends(get_all_teams), games_data: MLGame = Depends(get_all_games)):

    # use data to make charts
    x_opponents, y_winners, z_matchup_data, matchup_colors, hover_data = (
        matchup_heatmap_fig(games_df)
    )
    x_seasons, y_ranking_names, z_rankings, heatmap_colors = (
        all_time_ranking_fig(ranking_df)
    )
    x_data_bars, y_data_bars, bar_colors = all_time_wins_fig(games_df)

    return templates.TemplateResponse(
        'mildredleague/alltime.html',
        x_opponents=x_opponents,
        y_winners=y_winners,
        z_matchup_data=z_matchup_data,
        matchup_colors=matchup_colors,
        hover_data=hover_data,
        x_seasons=x_seasons,
        y_ranking_names=y_ranking_names,
        z_rankings=z_rankings,
        heatmap_colors=heatmap_colors,
        x_data_bars=x_data_bars,
        y_data_bars=y_data_bars,
        bar_colors=bar_colors,
    )


@ml_views.get("/rules", response_class=HTMLResponse)
def rules(request: Request):
    return templates.TemplateResponse(
        'mildredleague/rules.html',
    )


@ml_views.get("/{season}", response_class=HTMLResponse)
def season_page(request: Request, season: int):
    # grab games data from API
    games_data, response_code = get_season_games(season=season)
    games_df = pandas.DataFrame(games_data.json)

    # grab notes data from API
    notes, response_code = get_season_notes(season)

    # pull boxplot score data for the season
    x_data_for, y_data_for, color_data_for = season_boxplot(season, 'for')
    x_data_against, y_data_against, color_data_against = season_boxplot(season, 'against')

    if season == 2020:
        table = season_table_active(season, games_df)
    else:
        table = season_table(season, games_df)

    return templates.TemplateResponse(
        'mildredleague/season.html',
        notes=notes.json,
        table=table,
        season=season,
        x_data_for=x_data_for,
        y_data_for=y_data_for,
        color_data_for=color_data_for,
        x_data_against=x_data_against,
        y_data_against=y_data_against,
        color_data_against=color_data_against,
    )


@ml_views.get("/{season}/sim", response_class=HTMLResponse)
def seed_sim(request: Request, season: int):
    if True:
        return redirect(url_for('mildredleague.season_page', season=season))
    elif season != 2020:
        return "You can't simulate this season.", 404
    elif request.method == 'GET':
        return templates.TemplateResponse(
            'mildredleague/sim.html',
            season=season,
        )
    elif request.method == 'POST':
        # grab games data from API
        games_data, response_code = get_season_games(season=season)
        games_df = pandas.DataFrame(games_data.json).set_index('_id')

        # we're going to concatenate the API data with simulated data
        # that the user has chosen, so we can rerun tiebreakers
        winners_array = [
            request.form['sim_game_1'],
            request.form['sim_game_2'],
            request.form['sim_game_3'],
            request.form['sim_game_4'],
            request.form['sim_game_5'],
            request.form['sim_game_6'],
            request.form['sim_game_7'],
        ]
        sim_df = pandas.DataFrame(
            data=[
                [
                    'Division 6',
                    'Referees',
                    'AFC East',
                    'Division 6',
                    'Referees',
                    'AFC East',
                    'Referees',
                ],
                ['sim' for i in range(0, 7)],
                [
                    'Tarpey',
                    'Charles',
                    'Conti',
                    'Frank',
                    'mballen',
                    'Jake',
                    'Brad',
                ],
                [
                    winners_array.count('Tarpey')*20 + 80,
                    winners_array.count('Charles')*20 + 80,
                    winners_array.count('Conti')*20 + 80,
                    winners_array.count('Frank')*20 + 80,
                    winners_array.count('mballen')*20 + 80,
                    winners_array.count('Jake')*20 + 80,
                    winners_array.count('Brad')*20 + 80,
                ],
                ['sim' for i in range(0, 7)],
                [
                    'Division 6',
                    'Referees',
                    'AFC East',
                    'Division 6',
                    'AFC East',
                    'AFC East',
                    'Referees',
                ],
                ['sim' for i in range(0, 7)],
                [
                    'Brando',
                    'Mildred',
                    'Samik',
                    'Fonti',
                    'Sendzik',
                    'Kindy',
                    'Tommy',
                ],
                [
                    winners_array.count('Brando')*20 + 80,
                    winners_array.count('Mildred')*20 + 80,
                    winners_array.count('Samik')*20 + 80,
                    winners_array.count('Fonti')*20 + 80,
                    winners_array.count('Sendzik')*20 + 80,
                    winners_array.count('Kindy')*20 + 80,
                    winners_array.count('Tommy')*20 + 80,
                ],
                ['sim' for i in range(0, 7)],
                [0 for i in range(0, 7)],
                [2020 for i in range(0, 7)],
                [14 for i in range(0, 7)],
                [14 for i in range(0, 7)],
            ]
        ).transpose()
        sim_df.columns = games_df.columns.tolist()
        sim_df = pandas.concat([games_df, sim_df], ignore_index=True)

        table = season_table_active(season, sim_df)[[
            'division',
            'nick_name',
            'win_total',
            'loss_total',
            'tie_total',
            'division_rank',
            'playoff_seed',
        ]]

        return templates.TemplateResponse(
            'mildredleague/sim.html',
            winners=winners_array,
            table=table,
            sim=True,
        )
