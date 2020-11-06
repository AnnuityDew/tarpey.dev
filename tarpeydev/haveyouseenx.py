# import native Python packages
import csv
import datetime
import json
import os
import pytz

# import third party packages
from flask import Blueprint, render_template, request
from google.cloud import firestore
import numpy
import pandas
import plotly
import plotly.express as px

# import custom local stuff
from tarpeydev.plotly_style import tarpeydev_default


hysx_bp = Blueprint('haveyouseenx', __name__, url_prefix='/haveyouseenx')


@hysx_bp.route('/', methods=['GET', 'POST'])
@hysx_bp.route('/search', methods=['GET', 'POST'])
def search():
    # read backlog and visualizations
    backlog = read_backlog()
    treemap = system_treemap()

    return render_template(
        'haveyouseenx/search.html',
        df=backlog,
        treemap=treemap,
    )


@hysx_bp.route('/results', methods=['GET', 'POST'])
def results():
    search_term = request.form['search_term']
    backlog = read_backlog()
    return render_template(
        'haveyouseenx/results.html',
        df=backlog,
        search_term=search_term,
    )


def read_backlog():
    # file path
    backlog_path = os.path.join(
        os.getcwd(),
        'data',
        'haveyouseenx',
        'haveyouseenx_annuitydew.csv'
    )
    # read backlog
    backlog = pandas.read_csv(
        backlog_path,
        index_col='id',
        encoding='latin1'
    )

    return backlog


class Backlog:
    def __init__(self, backlog_owner):
        self.backlog_owner = backlog_owner
        self.backlog_dict = {}

    def add_game(self, backlog_game):
        self.backlog_dict[backlog_game.game_id] = backlog_game

    def remove_game(self, game_id):
        del self.backlog_dict[game_id]

    def from_csv(self, backlog_path):
        with open(backlog_path, encoding='latin1') as backlog_csv:
            eastern = pytz.timezone('US/Eastern')
            backlog_reader = csv.reader(backlog_csv)
            # skip header row
            next(backlog_reader)
            for row in backlog_reader:
                # convert date strings to datetime objects
                if row[10] != '':
                    row[10] = eastern.localize(datetime.datetime.strptime(row[10], '%m/%d/%y').replace(hour=12))
                if row[11] != '':
                    row[11] = eastern.localize(datetime.datetime.strptime(row[11], '%m/%d/%y').replace(hour=12))
                if row[12] != '':
                    row[12] = eastern.localize(datetime.datetime.strptime(row[12], '%m/%d/%y').replace(hour=12))
                if row[13] != '':
                    row[13] = eastern.localize(datetime.datetime.strptime(row[13], '%m/%d/%y').replace(hour=12))
                # convert empty strings to None
                row = [None if item == '' else item for item in row]
                game = BacklogGame(
                    game_id=row[0],
                    game_title=row[1],
                    sub_title=row[2],
                    game_system=row[3],
                    genre=row[4],
                    now_playing=row[5],
                    game_status=row[6],
                    game_hours=row[7],
                    game_minutes=row[8],
                    playtime_calc=row[9],
                    add_date=row[10],
                    start_date=row[11],
                    beat_date=row[12],
                    complete_date=row[13],
                    game_notes=row[14],
                )
                self.add_game(game)

    def from_pandas(self, backlog_df):
        backlog_df = backlog_df.where(pandas.notnull(backlog_df), None)
        eastern = pytz.timezone('US/Eastern')
        # convert strings to dates
        for index, row in backlog_df.iterrows():
            # convert date strings to Python datetime objects
            if row.add_date is not None:
                row.add_date = eastern.localize(datetime.datetime.strptime(row.add_date, '%m/%d/%y').replace(hour=12))
            if row.start_date is not None:
                row.start_date = eastern.localize(datetime.datetime.strptime(row.start_date, '%m/%d/%y').replace(hour=12))
            if row.beat_date is not None:
                row.beat_date = eastern.localize(datetime.datetime.strptime(row.beat_date, '%m/%d/%y').replace(hour=12))
            if row.complete_date is not None:
                row.complete_date = eastern.localize(datetime.datetime.strptime(row.complete_date, '%m/%d/%y').replace(hour=12))
            game = BacklogGame(
                game_id=index,
                game_title=row.game_title,
                sub_title=row.sub_title,
                game_system=row.game_system,
                genre=row.genre,
                now_playing=row.now_playing,
                game_status=row.game_status,
                game_hours=row.game_hours,
                game_minutes=row.game_minutes,
                playtime_calc=row.playtime_calc,
                add_date=row.add_date,
                start_date=row.start_date,
                beat_date=row.beat_date,
                complete_date=row.complete_date,
                game_notes=row.game_notes,
            )
            self.add_game(game)

    def to_firebase(self):
        db = firestore.Client()
        doc_ref = db.collection('backlogs').document(self.backlog_owner)
        for game_id, backlog_game in self.backlog_dict.items():
            doc_ref.collection('games').document(game_id).set(
                backlog_game.to_dict()
            )

    def print_backlog(self):
        print(f'Backlog(backlog_owner={self.backlog_owner})')
        for game_id, backlog_game in self.backlog_dict.items():
            print(f'{game_id}: {backlog_game.game_title}')


class BacklogGame:
    def __init__(self, game_id, game_title, game_system, genre,
                 now_playing, game_status, playtime_calc,
                 game_hours=0, game_minutes=0, sub_title=None,
                 add_date=None, start_date=None, beat_date=None,
                 complete_date=None, game_notes=None):
        self.game_id = game_id
        self.game_title = game_title
        self.sub_title = sub_title
        self.game_system = game_system
        self.genre = genre
        self.now_playing = now_playing
        self.game_status = game_status
        self.game_hours = game_hours
        self.game_minutes = game_minutes
        self.playtime_calc = playtime_calc
        self.add_date = add_date
        self.start_date = start_date
        self.beat_date = beat_date
        self.complete_date = complete_date
        self.game_notes = game_notes

    def to_dict(self):
        return self.__dict__

    def print_game(self):
        print(
            'BacklogGame(' + "\n    " +
            f'game_id={self.game_id}, ' +
            str(type(self.game_id)) + "\n    " +
            f'game_title={self.game_title}, ' +
            str(type(self.game_title)) + "\n    " +
            f'sub_title={self.sub_title}, ' +
            str(type(self.sub_title)) + "\n    " +
            f'game_system={self.game_system}, ' +
            str(type(self.game_system)) + "\n    " +
            f'genre={self.genre}, ' +
            str(type(self.genre)) + "\n    " +
            f'now_playing={self.now_playing}, ' +
            str(type(self.now_playing)) + "\n    " +
            f'game_status={self.game_status}, ' +
            str(type(self.game_status)) + "\n    " +
            f'game_hours={self.game_hours}, ' +
            str(type(self.game_hours)) + "\n    " +
            f'game_minutes={self.game_minutes}, ' +
            str(type(self.game_minutes)) + "\n    " +
            f'playtime_calc={self.playtime_calc}, ' +
            str(type(self.playtime_calc)) + "\n    " +
            f'add_date={self.add_date}, ' +
            str(type(self.add_date)) + "\n    " +
            f'start_date={self.start_date}, ' +
            str(type(self.start_date)) + "\n    " +
            f'beat_date={self.beat_date}, ' +
            str(type(self.beat_date)) + "\n    " +
            f'complete_date={self.complete_date}, ' +
            str(type(self.complete_date)) + "\n    " +
            f'game_notes={self.game_notes}, ' +
            str(type(self.game_notes)) + "\n" +
            ')'
        )


def system_treemap():
    # read backlog and create a count column
    backlog = read_backlog()
    backlog['count'] = 1
    # column to serve as the root of the backlog
    backlog['backlog'] = 'Backlog'
    # complete gametime calc
    backlog['game_hours'] = (
        backlog['game_hours'] + (backlog['game_minutes'] / 60)
    )

    # pivot table by gameSystem and gameStatus.
    # fill missing values with zeroes

    system_status_df = backlog.groupby(
        by=[
            'backlog',
            'game_system',
            'game_status',
        ]
    ).agg(
        {
            'count': sum,
            'game_hours': sum,
        }
    ).reset_index()

    figure = px.treemap(
        system_status_df,
        path=['backlog', 'game_status', 'game_system'],
        values='count',
        color=numpy.log10(system_status_df['game_hours']),
        color_continuous_scale=px.colors.diverging.Spectral_r,
        hover_data=['game_hours'],
        template=tarpeydev_default(),
    )

    # update margins and colors
    figure.update_layout(
        margin=dict(l=10, r=0, t=10, b=10),
    )
    figure.layout.coloraxis.colorbar = dict(
        title='Hours',
        tickvals=[1.0, 2.0, 3.0],
        ticktext=[10, 100, 1000],
    )

    # convert to JSON for the web
    figure_json = json.dumps(figure, cls=plotly.utils.PlotlyJSONEncoder)

    return figure_json
