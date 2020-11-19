# import native Python packages
import json
import os

# import third party packages
from flask import Blueprint, render_template
import numpy
import pandas
import plotly
import plotly.express as px
import plotly.figure_factory as ff
import plotly.graph_objects as go

# import custom local stuff
from tarpeydev import api


ml_bp = Blueprint('mildredleague', __name__, url_prefix='/mildredleague')


@ml_bp.route('/', methods=['GET'])
@ml_bp.route('/home', methods=['GET'])
def home():
    return render_template(
        'mildredleague/home.html',
    )


@ml_bp.route('/alltime', methods=['GET'])
def alltime():
    # grab data from API
    teams_data, response_code = api.all_teams_data(api=True)
    ranking_df = pandas.DataFrame(teams_data.json)

    # use data to make charts
    all_time_matchups_json = matchup_heatmap_fig()
    x_seasons, y_ranking_names, z_rankings, heatmap_colors = (
        all_time_ranking_fig(ranking_df)
    )
    x_data_bars, y_data_bars, bar_colors = all_time_wins_fig()

    return render_template(
        'mildredleague/alltime.html',
        matchups=all_time_matchups_json,
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
    # pull boxplot score data for the season
    x_data_for, y_data_for, color_data_for = season_boxplot(season, 'for')
    x_data_against, y_data_against, color_data_against = season_boxplot(season, 'against')
    notes = api.read_season_notes(season)
    table = season_table(season)

    return render_template(
        'mildredleague/season.html',
        notes=notes,
        table=table,
        season=season,
        x_data_for=x_data_for,
        y_data_for=y_data_for,
        color_data_for=color_data_for,
        x_data_against=x_data_against,
        y_data_against=y_data_against,
        color_data_against=color_data_against,
    )


def matchup_heatmap_fig():
    # pull all games ever
    all_games_df = all_games()
    # convert to record_df
    matchup_df = calc_matchup_records(
        all_games_df
    ).reset_index()
    # pull all-time file to filter active teams
    teams_data, response_code = api.all_teams_data(api=True)
    ranking_df = pandas.DataFrame(teams_data.json)

    # game total custom data for the hover text
    game_df = matchup_df.merge(
        ranking_df.loc[
            ranking_df.active == 1,
            ['nick_name']
        ].drop_duplicates(),
        left_on='winner',
        right_on='nick_name',
        how='inner',
    ).merge(
        ranking_df.loc[
            ranking_df.active == 1,
            ['nick_name']
        ].drop_duplicates(),
        left_on='loser',
        right_on='nick_name',
        how='inner',
    ).drop(
        columns=['nick_name_x', 'nick_name_y']
    ).set_index(keys=['winner', 'loser'])[['game_total']].unstack()

    # inner join will result in only active teams. unstack
    matchup_df = matchup_df.merge(
        ranking_df.loc[
            ranking_df.active == 1,
            ['nick_name']
        ].drop_duplicates(),
        left_on='winner',
        right_on='nick_name',
        how='inner',
    ).merge(
        ranking_df.loc[
            ranking_df.active == 1,
            ['nick_name']
        ].drop_duplicates(),
        left_on='loser',
        right_on='nick_name',
        how='inner',
    ).drop(
        columns=['nick_name_x', 'nick_name_y']
    ).set_index(keys=['winner', 'loser'])[['win_pct']].unstack()

    # start creating the figure!
    # y axis labels
    winners = matchup_df.index.to_list()
    # x axis labels
    opponents = matchup_df.columns.get_level_values(1).to_list()
    figure = go.Figure(
        data=go.Heatmap(
            z=matchup_df[['win_pct']],
            customdata=game_df[['game_total']],
            hovertemplate='Winner: %{y}<br>Opponent: %{x}<br>Win %: %{z:.3f}<br>Games: %{customdata} <extra></extra>',
            x=opponents,
            y=winners,
            colorscale=plotly.colors.diverging.Tropic,
        )
    )

    # update margins and colors
    figure.update_layout(
        title="Matchup Win Percentage (Active Teams)",
        margin=dict(l=120, r=60, t=150, autoexpand=True),
        # custom xaxis and yaxis titles
    )
    figure.update_xaxes(showgrid=False, showline=False, side='top', ticks='')
    figure.update_yaxes(showgrid=False, showline=False, ticks='')

    figure_json = json.dumps(figure, cls=plotly.utils.PlotlyJSONEncoder)

    return figure_json


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

    heatmap_colors = [[0, '#6baed6'], [1, '#08306b']]

    return x_seasons, y_ranking_names, z_rankings, heatmap_colors


def all_time_wins_fig():
    # pull all games ever
    all_games_df = all_games()
    # regular season df
    regular_df = all_games_df.loc[all_games_df.playoff == 0]
    # convert to record_df
    record_df = calc_records(
        regular_df
    ).reset_index().sort_values('win_total', ascending=True)

    # create list of x_data and y_data
    x_data = record_df.win_total.values.tolist()
    y_data = record_df.nick_name.values.tolist()
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
    boxplot_data, response_code = api.season_boxplot_retrieve(
        season,
        against,
        api=True,
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


def season_table(season):
    # pull games for the requested season
    season_games_df = all_games()
    season_games_df = season_games_df.loc[season_games_df.season == int(season)]

    # run calc records for the season
    season_records_df = calc_records(
        season_games_df
    ).reset_index()
    # pull all rankings and filter for the season
    teams_data, response_code = api.all_teams_data(api=True)
    season_ranking_df = pandas.DataFrame(teams_data.json)
    season_ranking_df = season_ranking_df.loc[season_ranking_df.season == int(season)]
    # merge playoff ranking and active status
    season_records_df = season_records_df.merge(
        season_ranking_df[['nick_name', 'playoff_rank', 'active']],
        on='nick_name',
        how='left',
    ).sort_values(
        by='playoff_rank', ascending=True
    )

    return season_records_df


def all_games():
    # read data for all games
    games_data, response_code = api.all_games_data(api=True)
    all_games_df = pandas.DataFrame(games_data.json)

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
    # season wins for away teams, home teams
    away_wins_for_df = pandas.pivot_table(games_df, values='a_win', index='a_nick', aggfunc='sum', fill_value=0)
    home_wins_for_df = pandas.pivot_table(games_df, values='h_win', index='h_nick', aggfunc='sum', fill_value=0)
    # season losses for away teams, home teams
    away_losses_for_df = pandas.pivot_table(games_df, values='h_win', index='a_nick', aggfunc='sum', fill_value=0)
    home_losses_for_df = pandas.pivot_table(games_df, values='a_win', index='h_nick', aggfunc='sum', fill_value=0)
    away_losses_for_df.rename(columns={'h_win': 'a_loss'}, inplace=True)
    home_losses_for_df.rename(columns={'a_win': 'h_loss'}, inplace=True)
    # ties
    away_ties_df = pandas.pivot_table(games_df, values='a_tie', index='a_nick', aggfunc='sum', fill_value=0)
    home_ties_df = pandas.pivot_table(games_df, values='h_tie', index='h_nick', aggfunc='sum', fill_value=0)
    # season points for for away teams, home teams
    away_points_for_df = pandas.pivot_table(games_df, values='a_score_norm', index='a_nick', aggfunc='sum', fill_value=0)
    home_points_for_df = pandas.pivot_table(games_df, values='h_score_norm', index='h_nick', aggfunc='sum', fill_value=0)
    # season points against for away teams, home teams
    away_points_against_df = pandas.pivot_table(games_df, values='h_score_norm', index='a_nick', aggfunc='sum', fill_value=0)
    home_points_against_df = pandas.pivot_table(games_df, values='a_score_norm', index='h_nick', aggfunc='sum', fill_value=0)
    away_points_against_df.rename(columns={'h_score_norm': 'a_score_norm_against'}, inplace=True)
    home_points_against_df.rename(columns={'a_score_norm': 'h_score_norm_against'}, inplace=True)
    # merge to one table
    record_df = home_wins_for_df.join(
        [
            away_wins_for_df,
            home_losses_for_df,
            away_losses_for_df,
            home_ties_df,
            away_ties_df,
            home_points_for_df,
            away_points_for_df,
            home_points_against_df,
            away_points_against_df,
        ],
        how='inner',
        ).rename_axis('nick_name')
    # win total, loss total, game total, points for, points against, win percentage
    record_df['win_total'] = record_df['h_win'] + record_df['a_win']
    record_df['loss_total'] = record_df['h_loss'] + record_df['a_loss']
    record_df['tie_total'] = record_df['h_tie'] + record_df['a_tie']
    record_df['games_played'] = record_df['win_total'] + record_df['loss_total'] + record_df['tie_total']
    record_df['win_pct'] = (record_df['win_total'] + record_df['tie_total'] * 0.5) / record_df['games_played']
    record_df['points_for'] = record_df['h_score_norm'] + record_df['a_score_norm']
    record_df['points_against'] = record_df['h_score_norm_against'] + record_df['a_score_norm_against']
    record_df['avg_margin'] = (record_df['points_for'] - record_df['points_against']) / record_df['games_played']
    record_df.sort_values(by='win_total', ascending=True, inplace=True)
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
    # grouping for away and home matchup winners
    away_wins_df = pandas.pivot_table(games_df, values='a_win', index=['a_nick', 'h_nick'], aggfunc='sum', fill_value=0)
    home_wins_df = pandas.pivot_table(games_df, values='h_win', index=['h_nick', 'a_nick'], aggfunc='sum', fill_value=0)
    # ties. only need to do this once since both teams receive a tie in a tie row
    away_ties_df = pandas.pivot_table(games_df, values='a_tie', index=['a_nick', 'h_nick'], aggfunc='sum', fill_value=0)
    home_ties_df = pandas.pivot_table(games_df, values='h_tie', index=['h_nick', 'a_nick'], aggfunc='sum', fill_value=0)
    # grouping for away and home matchup OCCURRENCES
    away_games_df = pandas.pivot_table(
        games_df, values='season', index=['a_nick', 'h_nick'], aggfunc='count', fill_value=0
    ).rename(columns={'season': 'a_games'})
    home_games_df = pandas.pivot_table(
        games_df, values='season', index=['h_nick', 'a_nick'], aggfunc='count', fill_value=0
    ).rename(columns={'season': 'h_games'})
    # rename indices
    away_wins_df.index.set_names(names=['winner', 'loser'], inplace=True)
    home_wins_df.index.set_names(names=['winner', 'loser'], inplace=True)
    away_ties_df.index.set_names(names=['winner', 'loser'], inplace=True)
    home_ties_df.index.set_names(names=['winner', 'loser'], inplace=True)
    away_games_df.index.set_names(names=['winner', 'loser'], inplace=True)
    home_games_df.index.set_names(names=['winner', 'loser'], inplace=True)
    # join and sum to get total matchup wins
    matchup_df = away_wins_df.join(
        [home_wins_df, away_ties_df, home_ties_df],
        how='outer',
    ).fillna(0).convert_dtypes()
    # ties count for 0.5
    matchup_df['win_total'] = (
        matchup_df['a_win'] +
        matchup_df['h_win'] +
        matchup_df['a_tie'] * 0.5 +
        matchup_df['h_tie'] * 0.5
    )
    # merge and sum to get total matchup occurrences
    total_matchup_df = away_games_df.join(
        [home_games_df],
        how='outer',
    ).fillna(0).convert_dtypes()
    total_matchup_df['game_total'] = total_matchup_df.sum(axis=1)
    # get rid of intermediate columns. just wins and games now
    matchup_df = matchup_df.join(
        total_matchup_df,
        how='outer',
    ).convert_dtypes().drop(
        columns=[
            'a_win',
            'h_win',
            'a_tie',
            'h_tie',
            'a_games',
            'h_games',
        ]
    )
    # add win pct column
    matchup_df['win_pct'] = matchup_df['win_total'] / matchup_df['game_total']

    return matchup_df
