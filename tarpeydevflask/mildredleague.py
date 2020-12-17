# import native Python packages
from itertools import permutations
import json

# import third party packages
from flask import (
    Blueprint, jsonify, redirect, render_template, request, url_for
)
import pandas
import plotly
import plotly.express as px
import pymongo

# import custom local stuff
from tarpeydevflask import api
from tarpeydevflask.db import MLGame, MLNote, get_dbm
from tarpeydevflask.users import login_required


ml_bp = Blueprint('mildredleague', __name__, url_prefix='/mildredleague')


@ml_bp.route('/', methods=['GET'])
@ml_bp.route('/home', methods=['GET'])
def home():
    return render_template(
        'mildredleague/home.html',
    )


@ml_bp.route('/alltime', methods=['GET'])
def alltime():
    # grab teams data from API
    teams_data, response_code = get_all_teams()
    ranking_df = pandas.DataFrame(teams_data.json)

    # grab games data from API
    games_data, response_code = get_all_games()
    games_df = pandas.DataFrame(games_data.json)

    # use data to make charts
    x_opponents, y_winners, z_matchup_data, matchup_colors, hover_data = (
        matchup_heatmap_fig(games_df)
    )
    x_seasons, y_ranking_names, z_rankings, heatmap_colors = (
        all_time_ranking_fig(ranking_df)
    )
    x_data_bars, y_data_bars, bar_colors = all_time_wins_fig(games_df)

    return render_template(
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


@ml_bp.route('/rules', methods=['GET'])
def rules():
    return render_template(
        'mildredleague/rules.html',
    )


@ml_bp.route('/<int:season>', methods=['GET'])
def season_page(season):
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

    return render_template(
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


@ml_bp.route('/<int:season>/sim', methods=['GET', 'POST'])
def seed_sim(season):
    if True:
        return redirect(url_for('mildredleague.season_page', season=season))
    elif season != 2020:
        return "You can't simulate this season.", 404
    elif request.method == 'GET':
        return render_template(
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

        return render_template(
            'mildredleague/sim.html',
            winners=winners_array,
            table=table,
            sim=True,
        )


@ml_bp.route('/add-game', methods=['GET', 'POST'])
@login_required
def add_game():
    if request.method == 'GET':
        next_id = api.auto_increment_mongo('mildredleague', 'games')
        return render_template(
            'mildredleague/add.html',
            next_id=next_id,
        )
    elif request.method == 'POST':
        client = get_dbm()
        db = client.mildredleague
        collection = db.games
        doc = MLGame(request.data).__dict__
        try:
            collection.insert_one(doc)
            # recalculate boxplot data for points for and against
            for boxplot in ['for', 'against']:
                season_boxplot_transform(
                    season=doc['season'],
                    against=boxplot,
                )
            return "Success! Added game " + str(doc['_id']) + ".", 200
        except pymongo.errors.DuplicateKeyError:
            return "Game " + str(doc['_id']) + " already exists!", 400


@ml_bp.route('/get-game/<int:game_id>', methods=['GET'])
@login_required
def get_game(game_id):
    client = get_dbm()
    db = client.mildredleague
    collection = db.games
    doc = list(collection.find({'_id': game_id}))
    if doc:
        return jsonify(doc[0]), 200
    else:
        return "No document found!", 400


@ml_bp.route('/edit-game', methods=['GET', 'PUT'])
@login_required
def edit_game():
    if request.method == 'GET':
        return render_template('mildredleague/edit.html')
    elif request.method == 'PUT':
        client = get_dbm()
        db = client.mildredleague
        collection = db.games
        doc = MLGame(request.data).__dict__
        collection.replace_one({'_id': doc['_id']}, doc)
        # recalculate boxplot data, points for and against
        for boxplot in ['for', 'against']:
            season_boxplot_transform(
                season=doc['season'],
                against=boxplot,
            )
        return "Success! Edited game " + str(doc['_id']) + ".", 200


@ml_bp.route('/delete-game/<int:game_id>', methods=['DELETE'])
@login_required
def delete_game(game_id):
    client = get_dbm()
    db = client.mildredleague
    collection = db.games
    doc = collection.find_one_and_delete({'_id': game_id})
    # recalculate boxplot data, points for and against
    for boxplot in ['for', 'against']:
        season_boxplot_transform(
            season=doc['season'],
            against=boxplot,
        )
    if doc:
        return "Success! Deleted game " + str(game_id) + ".", 200
    else:
        return "Something weird happened...", 400


@ml_bp.route('/teams/all', methods=['GET'])
@login_required
def get_all_teams():
    client = get_dbm()
    db = client.mildredleague
    collection = db.teams
    # return full history of mildredleague teams
    data = list(collection.find())
    if not data:
        return "No data found!", 400
    else:
        return jsonify(data), 200


@ml_bp.route('/games/all', methods=['GET'])
@login_required
def get_all_games():
    client = get_dbm()
    db = client.mildredleague
    collection = db.games
    # return full history of mildredleague games
    data = list(collection.find())
    if not data:
        return "No data found!", 400
    else:
        return jsonify(data), 200


@ml_bp.route('/games/<int:season>', methods=['GET'])
def get_season_games(season):
    client = get_dbm()
    db = client.mildredleague
    collection = db.games
    # return all results if no search_term
    data = list(collection.find({"season": season}))
    if not data:
        return "No data found!", 400
    else:
        return jsonify(data), 200


@ml_bp.route('/add-note', methods=['GET', 'POST'])
def add_note():
    if request.method == 'GET':
        next_id = api.auto_increment_mongo('mildredleague', 'notes')
        return render_template(
            'mildredleague/notes.html',
            next_id=next_id,
        )
    elif request.method == 'POST':
        client = get_dbm()
        db = client.mildredleague
        collection = db.notes
        doc = MLNote(request.data).__dict__
        try:
            collection.insert_one(doc)
            return "Success! Added note " + str(doc['_id']) + ".", 200
        except pymongo.errors.DuplicateKeyError:
            return "Note " + str(doc['_id']) + " already exists!", 400


@ml_bp.route('/get-note/<int:note_id>', methods=['GET'])
def get_note(note_id):
    client = get_dbm()
    db = client.mildredleague
    collection = db.notes
    doc = list(collection.find({'_id': note_id}))
    if doc:
        return jsonify(doc[0]), 200
    else:
        return "No document found!", 400


@ml_bp.route('/notes/<int:season>', methods=['GET'])
def get_season_notes(season):
    # fetch data from MongoDB
    client = get_dbm()
    db = client.mildredleague
    collection = db.notes
    # return all results if no search_term
    doc_list = list(collection.find({"season": season}))
    if doc_list:
        return jsonify(doc_list), 200
    else:
        return "No documents found!", 400


@ml_bp.route('/edit-note', methods=['GET', 'PUT'])
def edit_note():
    if request.method == 'GET':
        return render_template('mildredleague/notes.html')
    elif request.method == 'PUT':
        client = get_dbm()
        db = client.mildredleague
        collection = db.notes
        doc = MLNote(request.data).__dict__
        collection.replace_one({'_id': doc['_id']}, doc)
        return "Success! Edited note " + str(doc['_id']) + ".", 200


@ml_bp.route('/delete-note/<int:note_id>', methods=['DELETE'])
@login_required
def delete_note(note_id):
    client = get_dbm()
    db = client.mildredleague
    collection = db.notes
    result = collection.delete_one({'_id': note_id})
    if result.deleted_count > 1:
        return "You deleted more than one document...", 400
    elif result.deleted_count < 1:
        return "You didn't delete anything!", 400
    elif result.deleted_count == 1:
        return "Success! Deleted note " + str(note_id) + ".", 200
    else:
        return "Something weird happened...", 400


@ml_bp.route('/boxplot/<int:season>/<against>', methods=['GET'])
def season_boxplot_retrieve(season, against):
    # fetch data from MongoDB
    client = get_dbm()
    db = client.mildredleague
    collection = getattr(db, against + str(season))
    data = list(collection.find({"name": {'$ne': 'Bye'}}))
    if data:
        return jsonify(data), 200
    else:
        return "No data found!", 400


def season_boxplot_transform(season, against):
    '''Call this function when games are added/edited/deleted.

    Boxplot data is transformed and cached so boxplots can
    be rendered more efficiently by end users.

    '''
    # read season and teams data from api
    games_data, response_code = get_season_games(season=season)
    teams_data, response_code = get_all_teams()
    season_df = pandas.DataFrame(games_data.json)
    # normalized score columns for two-week playoff games
    season_df['a_score_norm'] = (
        season_df['a_score'] / (
            season_df['week_e'] - season_df['week_s'] + 1
        )
    )
    season_df['h_score_norm'] = (
        season_df['h_score'] / (
            season_df['week_e'] - season_df['week_s'] + 1
        )
    )
    # we just want unique scores. so let's stack away and home.
    # this code runs to analyze Points For.
    if against == 'for':
        score_df = season_df[['a_nick', 'a_score_norm']].rename(
            columns={'a_nick': 'name', 'a_score_norm': 'score'},
        ).append(
            season_df[['h_nick', 'h_score_norm']].rename(
                columns={'h_nick': 'name', 'h_score_norm': 'score'},
            ),
            ignore_index=True,
        )
    # this code runs to analyze Points Against.
    if against == 'against':
        score_df = season_df[['a_nick', 'h_score_norm']].rename(
            columns={'a_nick': 'name', 'h_score_norm': 'score'},
        ).append(
            season_df[['h_nick', 'a_score_norm']].rename(
                columns={'h_nick': 'name', 'a_score_norm': 'score'},
            ),
            ignore_index=True,
        )
    # let's sort by playoff rank instead
    # read season file, but we only need nick_name, season, and playoff_rank
    ranking_df = pandas.DataFrame(teams_data.json)[['nick_name', 'season', 'playoff_rank']]
    # merge this (filtered by season) into score_df so we can sort values
    score_df = score_df.merge(
        ranking_df.loc[ranking_df.season == int(season), ['nick_name', 'playoff_rank']],
        left_on=['name'],
        right_on=['nick_name'],
        how='left',
    ).sort_values(
        by='playoff_rank', ascending=True,
    )

    # add a unique _id for Mongo
    score_df['_id'] = range(1, len(score_df) + 1)

    # convert back to json for writing to Mongo
    doc_list = json.loads(score_df.to_json(orient='records'))

    # write data to MongoDB
    client = get_dbm()
    db = client.mildredleague
    collection = getattr(db, against + str(season))
    if list(collection.find()) == doc_list:
        message, response_code = str(season) + against + " boxplot chart is already synced!", 200
    else:
        # if boxplots need to be recalculated, just wipe the collection and reinsert
        collection.delete_many({})
        collection.insert_many(doc_list)
        message, response_code = "Bulk delete and insert complete!", 200

    return message, response_code


def matchup_heatmap_fig(games_df):
    # normalize games
    games_df = normalize_games(games_df)
    # convert to record_df
    matchup_df = calc_matchup_records(
        games_df
    ).reset_index()
    # pull all-time file to filter active teams
    teams_data, response_code = get_all_teams()
    ranking_df = pandas.DataFrame(teams_data.json)

    # inner joins are just to keep active teams
    active_matchup_df = matchup_df.merge(
        ranking_df.loc[
            ranking_df.active == 'yes',
            ['nick_name']
        ].drop_duplicates(),
        on='nick_name',
        how='inner',
    ).merge(
        ranking_df.loc[
            ranking_df.active == 'yes',
            ['nick_name']
        ].drop_duplicates(),
        left_on='loser',
        right_on='nick_name',
        how='inner',
    ).drop(
        columns=['nick_name_y']
    ).rename(
        columns={'nick_name_x': 'nick_name'}
    ).set_index(keys=['nick_name', 'loser'])

    # game total custom data for the hover text
    game_df = active_matchup_df[['game_total']].unstack()
    # win pct data is what drives the figure
    matchup_df = active_matchup_df[['win_pct']].unstack()

    # start creating the figure!
    # y axis labels
    y_winners = matchup_df.index.to_list()
    y_winners.reverse()
    # x axis labels
    x_opponents = matchup_df.columns.get_level_values(1).to_list()
    # z axis data, replacing nan with 0s
    z_matchup_data = matchup_df[['win_pct']].fillna(-1).values.tolist()
    z_matchup_data.reverse()
    # custom hovertext data, replacing nan with 0s
    hover_data = game_df[['game_total']].fillna(0).values.tolist()
    hover_data.reverse()
    # color data
    matchup_colors = [
        [i / (len(plotly.colors.diverging.Temps_r) - 1), color]
        for i, color in enumerate(plotly.colors.diverging.Temps_r)
    ]

    return x_opponents, y_winners, z_matchup_data, matchup_colors, hover_data


def all_time_ranking_fig(ranking_df):
    # pivot by year for all teams
    annual_ranking_df = pandas.pivot(
        ranking_df,
        index='nick_name',
        columns='season',
        values='playoff_rank'
    )

    # temporary variable to rank relevance of a team.
    # higher numbers are less relevant.
    # 15 for teams that didn't play in a given year
    # (worst rank for a team that existed would be 14)
    annual_ranking_df_temp = annual_ranking_df.fillna(15)
    annual_ranking_df_temp['relevance'] = annual_ranking_df_temp.sum(axis=1)
    annual_ranking_df['relevance'] = annual_ranking_df_temp['relevance']
    annual_ranking_df.sort_values(by='relevance', ascending=False, inplace=True)
    annual_ranking_df.reset_index(inplace=True)

    # y axis labels
    y_ranking_names = annual_ranking_df.nick_name.to_list()

    # drop unnecessary columns
    annual_ranking_df.drop(columns=['nick_name', 'relevance'], inplace=True)

    # x axis labels
    x_seasons = annual_ranking_df.columns.tolist()

    # need to pull out of data frame format for this particular figure,
    # and replace np.nan with 0 (to then replace with None)
    z_rankings = annual_ranking_df.fillna(0).values.tolist()

    heatmap_colors = [
        [i / (len(plotly.colors.diverging.Temps) - 1), color]
        for i, color in enumerate(plotly.colors.diverging.Temps)
    ]

    return x_seasons, y_ranking_names, z_rankings, heatmap_colors


def all_time_wins_fig(games_df):
    # regular season df
    regular_df = games_df.loc[games_df.playoff == 0]
    # convert to record_df
    record_df = calc_records(
        regular_df
    )
    # group by nick_name (don't need division info for this figure)
    record_df = record_df.groupby(
        level=['nick_name'],
    ).agg(
        {'win_total': sum}
    ).sort_values('win_total', ascending=True)

    # create list of x_data and y_data
    x_data = list(record_df.win_total.values)
    y_data = record_df.index.tolist()
    # color data needs to be tripled to have enough
    # colors for every bar!
    color_data = (
        px.colors.cyclical.Phase[1:] +
        px.colors.cyclical.Phase[1:] +
        px.colors.cyclical.Phase[1:]
    )

    return x_data, y_data, color_data


def season_boxplot(season, against):
    # grab data from API
    boxplot_data, response_code = season_boxplot_retrieve(
        season,
        against,
    )
    score_df = pandas.DataFrame(boxplot_data.json)

    # names on the X axis
    x_data = score_df.nick_name.unique().tolist()

    # Y axis is scores. need 2D array
    y_data = [
        score_df.loc[
            score_df.nick_name == name, 'score'
        ].tolist() for name in x_data
    ]

    # list of hex color codes
    color_data = px.colors.qualitative.Light24

    return x_data, y_data, color_data


def normalize_games(all_games_df):
    # which team won?
    all_games_df['a_win'] = 0
    all_games_df['h_win'] = 0
    all_games_df['a_tie'] = 0
    all_games_df['h_tie'] = 0
    # away win
    all_games_df.loc[all_games_df.a_score > all_games_df.h_score, 'a_win'] = 1
    # home win
    all_games_df.loc[all_games_df.a_score < all_games_df.h_score, 'h_win'] = 1
    # tie
    all_games_df.loc[all_games_df.a_score == all_games_df.h_score, ['a_tie', 'h_tie']] = 1
    # normalized score columns for two-week playoff games
    all_games_df['a_score_norm'] = (
        all_games_df['a_score'] / (
            all_games_df['week_e'] - all_games_df['week_s'] + 1
        )
    )
    all_games_df['h_score_norm'] = (
        all_games_df['h_score'] / (
            all_games_df['week_e'] - all_games_df['week_s'] + 1
        )
    )
    # margin = home - away
    all_games_df['h_margin'] = all_games_df['h_score_norm'] - all_games_df['a_score_norm']

    return all_games_df


def calc_records(games_df):
    # season wins/losses/ties/PF/PA for away teams, home teams
    away_df = pandas.pivot_table(
        games_df.convert_dtypes(),
        values=['a_win', 'h_win', 'a_tie', 'a_score_norm', 'h_score_norm'],
        index=['a_division', 'a_nick'],
        aggfunc='sum',
        fill_value=0
        )
    home_df = pandas.pivot_table(
        games_df.convert_dtypes(),
        values=['h_win', 'a_win', 'h_tie', 'h_score_norm', 'a_score_norm'],
        index=['h_division', 'h_nick'],
        aggfunc='sum',
        fill_value=0
        )

    # rename index and against columns
    away_df = away_df.rename(
        columns={'h_win': 'a_loss', 'h_score_norm': 'a_score_norm_against'},
    ).rename_axis(
        index={'a_nick': 'nick_name', 'a_division': 'division'}
    )
    home_df = home_df.rename(
        columns={'a_win': 'h_loss', 'a_score_norm': 'h_score_norm_against'},
    ).rename_axis(
        index={'h_nick': 'nick_name', 'h_division': 'division'}
    )
    # merge to one table
    record_df = home_df.join(
        away_df,
        how='inner',
        )
    # win total, loss total, game total, points for, points against, win percentage
    record_df['win_total'] = record_df['h_win'] + record_df['a_win']
    record_df['loss_total'] = record_df['h_loss'] + record_df['a_loss']
    record_df['tie_total'] = record_df['h_tie'] + record_df['a_tie']
    record_df['games_played'] = record_df['win_total'] + record_df['loss_total'] + record_df['tie_total']
    record_df['win_pct'] = (record_df['win_total'] + record_df['tie_total'] * 0.5) / record_df['games_played']
    record_df['points_for'] = record_df['h_score_norm'] + record_df['a_score_norm']
    record_df['points_against'] = record_df['h_score_norm_against'] + record_df['a_score_norm_against']
    record_df['avg_margin'] = (record_df['points_for'] - record_df['points_against']) / record_df['games_played']
    record_df.sort_values(by='win_pct', ascending=False, inplace=True)
    record_df.drop(
        columns=[
            'h_win',
            'a_win',
            'h_loss',
            'a_loss',
            'h_tie',
            'a_tie',
            'h_score_norm',
            'a_score_norm',
            'h_score_norm_against',
            'a_score_norm_against',
        ],
        inplace=True,
    )

    return record_df


def calc_matchup_records(games_df):
    # grouping for away and home matchup winners, ties, occurrences
    away_df = pandas.pivot_table(
        games_df,
        values=['a_win', 'a_tie', 'season'],
        index=['a_nick', 'h_nick'],
        aggfunc={
            'a_win': 'sum',
            'a_tie': 'sum',
            'season': 'count',
        },
        fill_value=0,
        ).rename(columns={'season': 'a_games'})
    home_df = pandas.pivot_table(
        games_df,
        values=['h_win', 'h_tie', 'season'],
        index=['h_nick', 'a_nick'],
        aggfunc={
            'h_win': 'sum',
            'h_tie': 'sum',
            'season': 'count',
        },
        fill_value=0,
        ).rename(columns={'season': 'h_games'})
    # rename indices
    away_df.index.set_names(names=['nick_name', 'loser'], inplace=True)
    home_df.index.set_names(names=['nick_name', 'loser'], inplace=True)
    # join and sum to get total matchup wins
    matchup_df = away_df.join(
        home_df,
        how='outer',
    ).fillna(0).convert_dtypes()
    # ties count for 0.5
    matchup_df['win_total'] = (
        matchup_df['a_win'] +
        matchup_df['h_win'] +
        matchup_df['a_tie'] * 0.5 +
        matchup_df['h_tie'] * 0.5
    )
    matchup_df['game_total'] = (
        matchup_df['a_games'] +
        matchup_df['h_games']
    )
    # get rid of intermediate columns. just wins and games now
    matchup_df = matchup_df.convert_dtypes().drop(
        columns=[
            'a_win',
            'h_win',
            'a_tie',
            'h_tie',
            'a_games',
            'h_games',
        ]
    )
    # add win pct column and sort by
    matchup_df['win_pct'] = matchup_df['win_total'] / matchup_df['game_total']
    matchup_df.sort_values(by=['win_pct'], ascending=False, inplace=True)

    return matchup_df


def season_table(season, games_df):
    # filter to games for the requested season
    games_df = normalize_games(games_df)
    games_df = games_df.loc[games_df.season == int(season)]

    # run calc records for the season
    season_records_df = calc_records(
        games_df
    ).reset_index()
    # pull all rankings and filter for the season
    teams_data, response_code = get_all_teams()
    season_ranking_df = pandas.DataFrame(teams_data.json)
    season_ranking_df = season_ranking_df.loc[season_ranking_df.season == int(season)]
    # merge playoff ranking and active status
    season_records_df = season_records_df.merge(
        season_ranking_df[['nick_name', 'playoff_rank', 'active']],
        on='nick_name',
        how='left',
    ).sort_values(
        by=['playoff_rank', 'loss_total'], ascending=True
    )

    return season_records_df


def season_table_active(season, games_df):
    '''Only use this function for the active season, to
    resolve tiebreakers.'''
    # filter to games for the requested season
    games_df = normalize_games(games_df)
    games_df = games_df.loc[games_df.season == int(season)]

    # to resolve tiebreakers, need records for the season
    season_records_df = calc_records(
        games_df
    )
    # also bring in H2H matchup records
    matchup_df = calc_matchup_records(
        games_df
    )

    # initial division ranking before tiebreakers.
    season_records_df['division_rank'] = season_records_df.groupby(
        level=['division'],
    )['win_pct'].rank(
        method='min',
        ascending=False,
    )

    # begin loop to resolve division ties.
    for div in season_records_df.index.unique(level='division'):
        # filter down to the division of interest.
        div_df = season_records_df.loc[[div]]
        # let's calculate division record here
        div_matchups = list(permutations(div_df.index.get_level_values('nick_name'), 2))
        # group by winner to determine H2H among the group
        div_matchup_df = matchup_df.loc[div_matchups].groupby(
            level='nick_name'
        ).agg(
            {'win_total': sum, 'game_total': sum}
        )
        # win_pct in the divisional grouping, then join back to div_df
        div_matchup_df['win_pct_div'] = (
            div_matchup_df['win_total'] / div_matchup_df['game_total']
        )
        div_df = div_df.join(div_matchup_df[['win_pct_div']])
        # loop over division_rank to determine where ties need to be broken.
        for rank in div_df.division_rank.unique():
            # if the length of the df is longer than 1 for any rank, there's a tie...
            tied_df = div_df.loc[div_df.division_rank == rank]
            if len(tied_df) > 1:
                untied_df = division_tiebreaker_one(tied_df, games_df, matchup_df)
                div_df.update(untied_df)
        season_records_df.update(div_df)

    # begin to determine playoff seed. first, separate the three division winners.
    div_winners_df = season_records_df.loc[season_records_df.division_rank == 1]
    div_losers_df = season_records_df.loc[season_records_df.division_rank > 1]
    # calculate initial seeding based on pure win_pct.
    div_winners_df['playoff_seed'] = div_winners_df.win_pct.rank(
        method='min',
        ascending=False,
    )
    div_losers_df['playoff_seed'] = div_losers_df.win_pct.rank(
        method='min',
        ascending=False,
    ) + len(div_winners_df)

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

    season_table = pandas.concat(
        [div_winners_df, div_losers_df]
    ).sort_values(
        by='playoff_seed'
    )

    return season_table.reset_index()


def division_tiebreaker_one(tied_df, games_df, matchup_df):
    # figure out who's got H2H among the 2+ teams by generating all possible matchups
    matchups = list(permutations(tied_df.index.get_level_values('nick_name'), 2))
    # group by winner to determine H2H among the group
    matchup_df = matchup_df.loc[matchups].groupby(
        level='nick_name'
    ).agg(
        {'win_total': sum, 'game_total': sum}
    )
    # win_pct in this H2H grouping
    matchup_df['win_pct_h2h'] = matchup_df['win_total'] / matchup_df['game_total']
    matchup_df['tiebreaker_rank'] = matchup_df.win_pct_h2h.rank(
        method='min',
        ascending=False,
    ) - 1

    # recalculate div rank now
    tied_df = tied_df.join(matchup_df[['tiebreaker_rank']])
    tied_df['division_rank'] = tied_df['division_rank'] + tied_df['tiebreaker_rank']

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
    tied_df['tiebreaker_two_rank'] = tied_df.win_pct_div.rank(
        method='min',
        ascending=False,
    ) - 1

    # recalculate div rank now
    tied_df['division_rank'] = tied_df['division_rank'] + tied_df['tiebreaker_two_rank']

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
    tied_df['tiebreaker_three_rank'] = tied_df.points_for.rank(
        method='min',
        ascending=False,
    ) - 1

    # recalculate div rank now
    tied_df['division_rank'] = tied_df['division_rank'] + tied_df['tiebreaker_three_rank']

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
    tied_df['tiebreaker_four_rank'] = tied_df.points_against.rank(
        method='min',
        ascending=False,
    ) - 1

    # recalculate div rank now
    tied_df['division_rank'] = tied_df['division_rank'] + tied_df['tiebreaker_four_rank']

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
    if len(tied_df.index.unique(level='division')) == 1:
        tied_df['playoff_seed'] = tied_df.division_rank.rank(
            method='min',
            ascending=True,
        ) + seed_to_break - 1
    else:
        # with two or more divisions involved, it's on to H2H record.
        # but we can only compare the top remaining team in each division.
        # here we need to filter any team that doesn't meet that criteria
        # and add one to their playoff seed, so they'll be included
        # in the next tiebreaker sequence.
        # let's do a groupby object to get the min division rank in each
        # division.
        filter_df = tied_df.groupby(
            'division'
            ).agg(
                {'division_rank': min}
            ).rename(
                columns={'division_rank': 'qualifying_rank'}
            )
        # if we're looping back through here after a qualifying rank was
        # determined in an earlier tiebreak for the same seed, this join will blow up
        # (we don't need to recalculate the qualifying rank until looking
        # at the next seed). so check for qualifying rank here before joining
        if 'qualifying_rank' not in tied_df.columns:
            tied_df = tied_df.join(filter_df)
        # split the tied_df here between teams that qualify to continue
        # the tiebreaker and teams that have to wait for the next seed
        qualified_tied_df = tied_df.loc[tied_df.division_rank == tied_df.qualifying_rank]
        disqualified_tied_df = tied_df.loc[tied_df.division_rank != tied_df.qualifying_rank]

        # send qualified teams to the next tiebreaker. when they return, concat
        # with the disqualified teams
        untied_df = wild_card_tiebreaker_two(qualified_tied_df, games_df, matchup_df, seed_to_break)

        # for wild card seeds, only one team can advance at a time.
        # the rest of the remaining teams have to be reconsidered in the next
        # seed's tiebreaker, so we reset seeds that weren't really tiebroken here.
        disqualified_tied_df['playoff_seed'] = seed_to_break + 1

        # concat happens here inside the update
        tied_df.update(pandas.concat([untied_df, disqualified_tied_df]))

    return tied_df


def wild_card_tiebreaker_two(tied_df, games_df, matchup_df, seed_to_break):
    # figure out who's got H2H among the 2-3 teams by generating all possible matchups
    matchups = list(permutations(tied_df.index.get_level_values('nick_name'), 2))
    # group by winner to determine H2H among the group
    wc_matchup_df = matchup_df.loc[matchup_df.index.intersection(matchups)].groupby(
        level='nick_name'
    ).agg(
        {'win_total': sum, 'game_total': sum}
    )
    # win_pct in this H2H grouping
    wc_matchup_df['win_pct_h2h'] = wc_matchup_df['win_total'] / wc_matchup_df['game_total']

    # our sweep check will just be whether or not game_total in a row is
    # 1 (in case of a 2-way tie) or 2 (in case of a 3-way tie). If it's not,
    # H2H will be skipped for that team (set win_pct_h2h to .500)
    wc_matchup_df.loc[
        wc_matchup_df.game_total < len(wc_matchup_df) - 1,
        'win_pct_h2h'] = 0.5

    # now determine H2H rank in the group
    wc_matchup_df['wc_tiebreaker_two_rank'] = wc_matchup_df.win_pct_h2h.rank(
        method='min',
        ascending=False,
    ) - 1

    # if we're looping back through here after a tiebreaker rank was
    # determined in an earlier tiebreak for the same seed, this join will blow up
    # so check for tiebreaker rank here before joining. if the column
    # is already there, just update it.
    if 'wc_tiebreaker_two_rank' not in tied_df.columns:
        tied_df = tied_df.join(wc_matchup_df[['wc_tiebreaker_two_rank']])
    else:
        tied_df.update(wc_matchup_df[['wc_tiebreaker_two_rank']])

    # if this is a two way tiebreaker where there was no H2H,
    # we'll have to fill in tiebreaker_two with zeroes
    # before we modify the playoff seed
    tied_df['wc_tiebreaker_two_rank'] = tied_df['wc_tiebreaker_two_rank'].fillna(0)

    # now modify playoff seed
    tied_df['playoff_seed'] = tied_df['playoff_seed'] + tied_df['wc_tiebreaker_two_rank']

    # for wild card seeds, only one team can advance at a time.
    # the rest of the remaining teams have to be reconsidered in the next
    # seed's tiebreaker, so we reset seeds that weren't really tiebroken here.
    tied_df.loc[tied_df.playoff_seed != seed_to_break, 'playoff_seed'] = seed_to_break + 1

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
    tied_df['wc_tiebreaker_three_rank'] = tied_df.points_for.rank(
        method='min',
        ascending=False,
    ) - 1

    # recalculate playoff seed now
    tied_df['playoff_seed'] = tied_df['playoff_seed'] + tied_df['wc_tiebreaker_three_rank']

    # for wild card seeds, only one team can advance at a time.
    # the rest of the remaining teams have to be reconsidered in the next
    # seed's tiebreaker, so we reset seeds that weren't really tiebroken here.
    tied_df.loc[tied_df.playoff_seed != seed_to_break, 'playoff_seed'] = seed_to_break + 1

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
    tied_df['wc_tiebreaker_four_rank'] = tied_df.points_against.rank(
        method='min',
        ascending=False,
    ) - 1

    # recalculate playoff seed now
    tied_df['playoff_seed'] = tied_df['playoff_seed'] + tied_df['wc_tiebreaker_four_rank']

    # for wild card seeds, only one team can advance at a time.
    # the rest of the remaining teams have to be reconsidered in the next
    # seed's tiebreaker, so we reset seeds that weren't really tiebroken here.
    tied_df.loc[tied_df.playoff_seed != seed_to_break, 'playoff_seed'] = seed_to_break + 1

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
