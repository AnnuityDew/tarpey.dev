# import native Python packages
import json

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
from tarpeydev.plotly_style import tarpeydev_default, tarpeydev_black


ml_bp = Blueprint('mildredleague', __name__, url_prefix='/mildredleague')


@ml_bp.route('/', methods=['GET'])
@ml_bp.route('/home', methods=['GET'])
def home():
    return render_template(
        'mildredleague/home.html',
    )


@ml_bp.route('/alltime', methods=['GET', 'POST'])
def alltime():
    # grab teams data from API
    teams_data, response_code = api.all_teams_data(api=True)
    ranking_df = pandas.DataFrame(teams_data.json)

    # grab games data from API
    games_data, response_code = api.all_games_data(api=True)
    games_df = pandas.DataFrame(games_data.json)

    # use data to make charts
    all_time_rankings_json = all_time_ranking_fig(ranking_df)
    all_time_matchups_json = matchup_heatmap_fig(games_df)
    all_time_wins_json = all_time_wins_fig(games_df)

    return render_template(
        'mildredleague/alltime.html',
        ranks=all_time_rankings_json,
        matchups=all_time_matchups_json,
        wins=all_time_wins_json,
    )


@ml_bp.route('/rules', methods=['GET'])
def rules():
    return render_template(
        'mildredleague/rules.html',
    )


@ml_bp.route('/<int:season>', methods=['GET', 'POST'])
def season_page(season):
    # grab games data from API
    games_data, response_code = api.all_games_data(api=True)
    games_df = pandas.DataFrame(games_data.json)

    # grab notes data from API
    notes = api.read_season_notes(season)

    # pull boxplot score data for the season
    boxplot_json_for = season_boxplot(season, 'for')
    boxplot_json_against = season_boxplot(season, 'against')
    table = season_table(season, games_df)

    return render_template(
        'mildredleague/season.html',
        boxplot_for=boxplot_json_for,
        boxplot_against=boxplot_json_against,
        notes=notes,
        table=table,
        season=season,
    )


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


def season_table(season, games_df):
    # filter to games for the requested season
    games_df = normalize_games(games_df)
    games_df = games_df.loc[games_df.season == int(season)]

    # run calc records for the season
    season_records_df = calc_records(
        games_df
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


def all_time_wins_fig(games_df):
    # pull all games ever
    games_df = normalize_games(games_df)
    # regular season df
    regular_df = games_df.loc[games_df.playoff == 0]
    # convert to record_df
    record_df = calc_records(
        regular_df
    ).reset_index().sort_values('win_total', ascending=True)

    figure = px.bar(
        record_df,
        x='win_total',
        y='nick_name',
        orientation='h',
        color='nick_name',
        template=tarpeydev_default(),
    )

    # generic bar chart so we can use our custom colors
    # instead of using plotly express
    figure = go.Figure()
    figure.update_layout(
        title="Regular Season Win Totals",
        margin=dict(l=120, r=60),
        xaxis=dict(
            title=None,
        ),
        yaxis=dict(
            title=None,
        ),
        showlegend=False,
        hovermode='closest',
        template=tarpeydev_default(),
    )
    # now convert the data to lists and add one at a time
    # to attach different colors in the cycle
    xy = record_df[['win_total', 'nick_name']].values.tolist()

    for i, bar in enumerate(xy):
        figure.add_trace(
            go.Bar(
                x=[xy[i][0]],
                y=[xy[i][1]],
                orientation='h',
                name=xy[i][1],
            )
        )

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
    nick_names = annual_ranking_df.nick_name.to_list()

    # drop unnecessary columns
    annual_ranking_df.drop(columns=['nick_name', 'relevance'], inplace=True)

    # x axis labels
    seasons = annual_ranking_df.columns.tolist()

    # need to pull out of data frame format for this particular figure
    annual_ranking_list = annual_ranking_df.values.tolist()

    # need a separate set for the annotations to look good
    ranking_annotations = annual_ranking_df.values.tolist()

    # convert to Int64 and blanks for the actual annotations
    for i, player in enumerate(ranking_annotations):
        for j, annual_result in enumerate(player):
            if numpy.isnan(annual_result):
                ranking_annotations[i][j] = ''
            else:
                ranking_annotations[i][j] = int(annual_result)

    # set up the figure and its axes
    figure = ff.create_annotated_heatmap(
        annual_ranking_list,
        x=seasons,
        y=nick_names,
        annotation_text=ranking_annotations,
        # subset of px.colors.sequential.Blues
        colorscale=[
            'rgb(107,174,214)',
            'rgb(66,146,198)',
            'rgb(33,113,181)',
            'rgb(8,81,156)',
            'rgb(8,48,107)',
        ],
    )

    # update margins and colors
    figure.update_layout(
        title="Mildred League Placements by Season",
        template=tarpeydev_black(),
        margin=dict(l=120, r=60),
    )
    figure.update_xaxes(showgrid=False, showline=False)
    figure.update_yaxes(showgrid=False, showline=False)

    # convert to JSON for the web
    figure_json = json.dumps(figure, cls=plotly.utils.PlotlyJSONEncoder)

    return figure_json


def matchup_heatmap_fig(games_df):
    # pull all games ever
    games_df = normalize_games(games_df)
    # convert to record_df
    matchup_df = calc_matchup_records(
        games_df
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
        template=tarpeydev_default(),
        margin=dict(l=120, r=60, t=150, autoexpand=True),
        # custom xaxis and yaxis titles
    )
    figure.update_xaxes(showgrid=False, showline=False, side='top', ticks='')
    figure.update_yaxes(showgrid=False, showline=False, ticks='')

    figure_json = json.dumps(figure, cls=plotly.utils.PlotlyJSONEncoder)

    return figure_json


def season_boxplot(season, against):
    # grab data
    boxplot_data, response_code = api.season_boxplot_retrieve(season, against, api=True)
    score_df = pandas.DataFrame(boxplot_data.json)

    # plotly boxplot!
    figure = px.box(
        score_df,
        x="name",
        y="score",
        color="name",
        color_discrete_sequence=px.colors.qualitative.Light24,
        points="all",
        title=str(season) + " Scores (" + against + ")",
        template=tarpeydev_default()
    )

    # turn off names at the bottom
    figure.update_xaxes(showticklabels=False)

    # update margins and colors
    figure.update_layout(
        xaxis_title=None,
        margin=dict(l=70, r=50, t=60, b=30),
        legend=dict(
            orientation='h',
            y=0,
            xanchor='left',
            x=0,
        ),
    )

    # convert to JSON for the web
    figure_json = json.dumps(figure, cls=plotly.utils.PlotlyJSONEncoder)

    return figure_json
