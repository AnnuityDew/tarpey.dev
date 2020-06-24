# import native Python packages
import base64
import functools
import io
import json
import os

# import third party packages
from flask import Blueprint, render_template, request
import numpy
import pandas
import plotly
import plotly.express as px
import seaborn


ml_bp = Blueprint('mildredleague', __name__, url_prefix='/mildredleague')


@ml_bp.route('/', methods=['GET', 'POST'])
@ml_bp.route('/home', methods=['GET', 'POST'])
def home():
    return render_template(
        'mildredleague/home.html',
    )


@ml_bp.route('/alltime', methods=['GET', 'POST'])
def alltime():
    # grab charts
    all_time_wins = all_time_records()
    all_time_rankings = all_time_ranking()

    # generate image from figure and save to buffer
    buffer = io.BytesIO()
    all_time_wins.savefig(
        buffer,
        format="png",
        facecolor='black',
    )
    all_time_win_data = base64.b64encode(buffer.getbuffer()).decode("ascii")

    # generate image from figure and save to buffer
    buffer = io.BytesIO()
    all_time_rankings.savefig(
        buffer,
        format="png",
        facecolor='black',
    )
    all_time_rank_data = base64.b64encode(buffer.getbuffer()).decode("ascii")
    
    return render_template(
        'mildredleague/alltime.html',
        wins=f"<img src='data:image/png;base64,{all_time_win_data}'/>",
        ranks=f"<img src='data:image/png;base64,{all_time_rank_data}'/>",
    )
    

def all_time_records():
    # read each season's summary of games
    season_files = [
        'mlgames2013.csv',
        'mlgames2014.csv',
        'mlgames2015.csv',
        'mlgames2016.csv',
        'mlgames2017.csv',
        'mlgames2018.csv',
        'mlgames2019.csv',
    ]

    # empty dataframe for all games
    all_games_df = pandas.DataFrame()

    # for each CSV, append to the all games dataframe
    for season_file in season_files:
        # file path construction
        season_path = os.path.join(
            os.getcwd(),
            'data',
            'mildredleague',
            season_file
        )
        # read season file
        season_df = pandas.read_csv(
            season_path,
        )
        if all_games_df.empty is True:
            all_games_df = season_df
        else:
            all_games_df = all_games_df.append(
                season_df,
                ignore_index=True,
            )

    # fix datatypes
    all_games_df = all_games_df.convert_dtypes()

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
    # regular season and postseason df
    regular_df = all_games_df.loc[all_games_df.playoff == 0]
    postseason_df = all_games_df.loc[all_games_df.playoff == 1]

    # regular season wins for away teams, home teams
    away_wins_for_df = pandas.pivot_table(regular_df, values='a_win', index='a_name', aggfunc='sum', fill_value=0)
    home_wins_for_df = pandas.pivot_table(regular_df, values='h_win', index='h_name', aggfunc='sum', fill_value=0)
    # regular season losses for away teams, home teams
    away_losses_for_df = pandas.pivot_table(regular_df, values='h_win', index='a_name', aggfunc='sum', fill_value=0)
    home_losses_for_df = pandas.pivot_table(regular_df, values='a_win', index='h_name', aggfunc='sum', fill_value=0)
    away_losses_for_df.rename(columns={'h_win': 'a_loss'}, inplace=True)
    home_losses_for_df.rename(columns={'a_win': 'h_loss'}, inplace=True)
    # ties
    away_ties_df = pandas.pivot_table(regular_df, values='a_tie', index='a_name', aggfunc='sum', fill_value=0)
    home_ties_df = pandas.pivot_table(regular_df, values='h_tie', index='h_name', aggfunc='sum', fill_value=0)
    # merge to one table
    record_df = home_wins_for_df.merge(
        away_wins_for_df, left_index=True, right_index=True
    ).merge(
        home_losses_for_df, left_index=True, right_index=True
    ).merge(
        away_losses_for_df, left_index=True, right_index=True
    ).merge(
        home_ties_df, left_index=True, right_index=True
    ).merge(
        away_ties_df, left_index=True, right_index=True
    )
    # win total, loss total, game total, win percentage
    record_df['win_total'] = record_df['h_win'] + record_df['a_win']
    record_df['loss_total'] = record_df['h_loss'] + record_df['a_loss']
    record_df['tie_total'] = record_df['h_tie'] + record_df['a_tie']
    record_df['games_played'] = record_df['win_total'] + record_df['loss_total'] + record_df['tie_total']
    record_df['win_pct'] = (record_df['win_total'] + record_df['tie_total'] * 0.5) / record_df['games_played']
    record_df.sort_values(by='win_total', ascending=True, inplace=True)

    # N = number of systems. for spacing out the bars
    N = len(record_df.index)
    # use numpy arange for x locations. evenly spaced out bars
    spacing = numpy.arange(N)

    # set up the figure and its axes
    figure = Figure(
        figsize=(8, 8),
    )
    ax = figure.subplots(
        nrows=1,
        ncols=1,
    )

    # how many colors do we need?
    bar_color_count = len(record_df.index)
    
    # generate a [0,1] range evenly spaced
    bar_range = range(0, bar_color_count)
    color_list = []
    for number in bar_range:
        color_list.append((number + 1) / bar_color_count)
    # generate the color array
    color_array = cm.PiYG(color_list)

    # barh
    bars = ax.barh(
        y=spacing,
        width=record_df['win_total'],
        tick_label=record_df.index,
        color=color_array,
    )

    # figure and chart background colors
    figure.set_facecolor('black')
    ax.set_facecolor('black')

    # title and title color
    ax.set_title("All-time Win Totals")
    ax.title.set_color('white')

    # axis colors
    ax.spines['bottom'].set_color('white')
    ax.spines['left'].set_color('white')

    # tick label colors
    ax.tick_params(axis='both', colors='white')

    # annotate with win totals
    for bar in bars:
        width = bar.get_width()
        ax.annotate(
            '{}'.format(width),
            xy=(width, bar.get_y()),
            xytext=(2, 4),  # 2 points x and 3 points y offset
            textcoords="offset points",
            color='white',
        )

    # optimize chart spacing
    figure.tight_layout()

    return figure


def all_time_ranking():
    # file path construction
    all_time_path = os.path.join(
        os.getcwd(),
        'data',
        'mildredleague',
        'mlalltime.csv'
    )
    # read season file
    ranking_df = pandas.read_csv(
        all_time_path,
    )

    # ranking by year for all teams
    annual_ranking_df = pandas.pivot(
        ranking_df,
        index='full_name',
        columns='year',
        values='playoff_rank'
    )

    # temporary variable to rank relevance of a team.
    # higher numbers are less relevant.
    # 15 for teams that didn't play in a given year
    # (worst rank for a team that existed would be 14)
    annual_ranking_df_temp = annual_ranking_df.fillna(15)
    annual_ranking_df_temp['relevance'] = annual_ranking_df_temp.sum(axis=1)
    annual_ranking_df['relevance'] = annual_ranking_df_temp['relevance']
    annual_ranking_df.sort_values(by='relevance', inplace=True)
    annual_ranking_df.drop(columns='relevance', inplace=True)

    # set up the figure and its axes
    figure = Figure(
        figsize=(8, 8),
    )
    ax = figure.subplots(
        nrows=1,
        ncols=1,
    )

    # draw heatmap with existing axis object
    # colormap reversed
    seaborn.heatmap(
        data=annual_ranking_df,
        cmap='Blues',
        annot=True,
        cbar=False,
        ax=ax,
        square=False,
    )

    # fix rotation of tick labels
    ax.tick_params(axis='x', colors='white', rotation=0, bottom=False)
    ax.tick_params(axis='y', colors='white', rotation=0, left=False)

    # figure and chart background colors
    figure.set_facecolor('black')
    ax.set_facecolor('black')

    # title and title color
    ax.set_title("Mildred League Placements by Season")
    ax.title.set_color('white')

    # axis colors
    ax.spines['bottom'].set_color('white')
    ax.spines['left'].set_color('white')

    # optimize chart spacing
    figure.tight_layout()

    return figure


@ml_bp.route('/2013', methods=['GET', 'POST'])
def season_2013():
    # pull boxplot score data for the season. True=against, False=for
    boxplot_json_for = season_boxplot('2013', False)
    boxplot_json_against = season_boxplot('2013', True)

    return render_template(
        'mildredleague/2013.html',
        boxplot_for=boxplot_json_for,
        boxplot_against=boxplot_json_against,
    )


@ml_bp.route('/2014', methods=['GET', 'POST'])
def season_2014():
    # pull boxplot score data for the season
    boxplot_json_for = season_boxplot('2014', False)
    boxplot_json_against = season_boxplot('2014', True)

    return render_template(
        'mildredleague/2014.html',
        boxplot_for=boxplot_json_for,
        boxplot_against=boxplot_json_against,
    )


@ml_bp.route('/2015', methods=['GET', 'POST'])
def season_2015():
    # pull boxplot score data for the season
    boxplot_json_for = season_boxplot('2015', False)
    boxplot_json_against = season_boxplot('2015', True)

    return render_template(
        'mildredleague/2015.html',
        boxplot_for=boxplot_json_for,
        boxplot_against=boxplot_json_against,
    )


@ml_bp.route('/2016', methods=['GET', 'POST'])
def season_2016():
    # pull boxplot score data for the season
    boxplot_json_for = season_boxplot('2016', False)
    boxplot_json_against = season_boxplot('2016', True)

    return render_template(
        'mildredleague/2016.html',
        boxplot_for=boxplot_json_for,
        boxplot_against=boxplot_json_against,
    )


@ml_bp.route('/2017', methods=['GET', 'POST'])
def season_2017():
    # pull boxplot score data for the season
    boxplot_json_for = season_boxplot('2017', False)
    boxplot_json_against = season_boxplot('2017', True)

    return render_template(
        'mildredleague/2017.html',
        boxplot_for=boxplot_json_for,
        boxplot_against=boxplot_json_against,
    )


@ml_bp.route('/2018', methods=['GET', 'POST'])
def season_2018():
    # pull boxplot score data for the season
    boxplot_json_for = season_boxplot('2018', False)
    boxplot_json_against = season_boxplot('2018', True)

    return render_template(
        'mildredleague/2018.html',
        boxplot_for=boxplot_json_for,
        boxplot_against=boxplot_json_against,
    )


@ml_bp.route('/2019', methods=['GET', 'POST'])
def season_2019():
    # pull boxplot score data for the season
    boxplot_json_for = season_boxplot('2019', False)
    boxplot_json_against = season_boxplot('2019', True)

    return render_template(
        'mildredleague/2019.html',
        boxplot_for=boxplot_json_for,
        boxplot_against=boxplot_json_against,
    )


def season_boxplot(year, against=True):
    # read the selected season as a dataframe
    season_path = os.path.join(
        os.getcwd(),
        'data',
        'mildredleague',
        'mlgames' + year + '.csv',
    )
    # read season file
    season_df = pandas.read_csv(
        season_path,
    )
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
    if against is False:
        score_df = season_df[['a_name', 'a_score_norm']].rename(
            columns={'a_name': 'name', 'a_score_norm': 'score'},
        ).append(
            season_df[['h_name', 'h_score_norm']].rename(
                columns={'h_name': 'name', 'h_score_norm': 'score'},
            ),
            ignore_index=True,
        )
        title_label='(Points For)'
    # this code runs to analyze Points Against.
    if against is True:
        score_df = season_df[['a_name', 'h_score_norm']].rename(
            columns={'a_name': 'name', 'h_score_norm': 'score'},
        ).append(
            season_df[['h_name', 'a_score_norm']].rename(
                columns={'h_name': 'name', 'a_score_norm': 'score'},
            ),
            ignore_index=True,
        )
        title_label='(Points Against)'
    # let's sort by playoff rank instead
    all_time_path = os.path.join(
        os.getcwd(),
        'data',
        'mildredleague',
        'mlalltime.csv'
    )
    # read season file, but we only need full_name, year, and playoff_rank
    ranking_df = pandas.read_csv(
        all_time_path,
    )[['full_name', 'year', 'playoff_rank']]
    # merge this (filtered by year) into score_df so we can sort values
    score_df = score_df.merge(
        ranking_df.loc[ranking_df.year == int(year), ['full_name', 'playoff_rank']],
        left_on=['name'],
        right_on=['full_name'],
        how='left',
    ).sort_values(
        by='playoff_rank', ascending=True,
    )

    # sort the dataframe by each team's mean score for the year
    # sort_df = score_df.groupby(by='name').mean().sort_values(by='score', ascending=False)
    # sort_df['rank'] = sort_df.rank(axis='index').rename(columns={'score': 'rank'})
    # sort_df.drop(columns='score', inplace=True)
    # score_df = score_df.merge(
    #     sort_df, on='name', how='left'
    # ).sort_values(
    #     by='rank', ascending=False,
    # )

    # plotly boxplot!
    figure = px.box(
        score_df,
        x="name",
        y="score",
        color="name",
        color_discrete_sequence=px.colors.cyclical.Phase,
        points="all",
        title=year + " Score Distribution " + title_label,
        height=500,
        width=800,
    )

    # turn off names at the bottom
    figure.update_xaxes(showticklabels=False)

    # update margins and colors
    figure.update_layout(
        autosize=True,
        xaxis_title=None,
        margin=dict(l=70, r=50, t=60, b=30),
    )
    figure.layout.paper_bgcolor = 'rgba(0,0,0,0)'
    figure.layout.plot_bgcolor = 'rgba(255,255,255,0.85)'
    figure.layout.font = dict(color='#FFFFFF')
    figure.layout.hoverlabel.font = dict(color='#FFFFFF')

    # convert to JSON for the web
    figure_json = json.dumps(figure, cls=plotly.utils.PlotlyJSONEncoder)

    return figure_json


@ml_bp.route('/rules', methods=['GET', 'POST'])
def rules():
    return render_template(
        'mildredleague/rules.html',
    )
