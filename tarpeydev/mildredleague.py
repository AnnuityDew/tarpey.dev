# import native Python packages
import base64
import functools
import io
import os

# import third party packages
from flask import Blueprint, render_template, request
from matplotlib import cm, rcParams
from matplotlib.colors import Normalize
from matplotlib.figure import Figure
import numpy
import pandas
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
    all_time_wins = read_season_stats()

    # generate image from figure and save to buffer
    buffer = io.BytesIO()
    all_time_wins.savefig(
        buffer,
        format="png",
        facecolor='black',
    )
    all_time_win_data = base64.b64encode(buffer.getbuffer()).decode("ascii")
    return render_template(
        'mildredleague/alltime.html',
        wins=f"<img src='data:image/png;base64,{all_time_win_data}'/>",
    )


@ml_bp.route('/2013', methods=['GET', 'POST'])
def season_2013():
    return render_template(
        'mildredleague/2013.html',
    )
    

def read_season_stats():
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
            'tarpeydev',
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


@ml_bp.route('/2014', methods=['GET', 'POST'])
def season_2014():
    return render_template(
        'mildredleague/2014.html',
    )


@ml_bp.route('/2015', methods=['GET', 'POST'])
def season_2015():
    return render_template(
        'mildredleague/2015.html',
    )


@ml_bp.route('/2016', methods=['GET', 'POST'])
def season_2016():
    return render_template(
        'mildredleague/2016.html',
    )


@ml_bp.route('/2017', methods=['GET', 'POST'])
def season_2017():
    return render_template(
        'mildredleague/2017.html',
    )


@ml_bp.route('/2018', methods=['GET', 'POST'])
def season_2018():
    return render_template(
        'mildredleague/2018.html',
    )


@ml_bp.route('/2019', methods=['GET', 'POST'])
def season_2019():
    return render_template(
        'mildredleague/2019.html',
    )


@ml_bp.route('/rules', methods=['GET', 'POST'])
def rules():
    return render_template(
        'mildredleague/rules.html',
    )
