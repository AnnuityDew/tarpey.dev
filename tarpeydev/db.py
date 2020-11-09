# import native Python packages
import click
import csv
import datetime
import os
import pytz

# import third party packages
from flask import current_app, g
from flask.cli import with_appcontext
from google.cloud import firestore
import pymongo
from pymongo import MongoClient


def get_dbf():
    '''Retrieve the firestore db.

    g is a special object that is unique for each request.
    It is used to store data that might be accessed by multiple
    functions during the request. The connection is stored and
    reused instead of creating a new connection if get_db is
    called a second time in the same request.

    '''

    if 'dbf' not in g:
        g.dbf = firestore.Client()
    return g.dbf


def close_dbf(e=None):
    '''Close the firestore db (if it's open).'''

    dbf = g.pop('dbf', None)

    if dbf is not None:
        dbf.close()


def get_dbm():
    '''Retrieve the MongoDB backlogs.'''

    if 'dbm' not in g:
        g.client = MongoClient(current_app.config['BACKLOGS_KEY'])
        g.dbm = g.client.backlogs

    return g.dbm, g.client


def close_dbm(e=None):
    '''Close the MongoDB (if it's open).'''

    client = g.pop('client', None)

    if client is not None:
        client.close()


def get_users():
    '''Retrieve the MongoDB users.'''

    if 'dbu' not in g:
        g.client = MongoClient(current_app.config['AUTH_KEY'])
        g.dbu = g.client.users

    return g.dbu, g.client


def close_users(e=None):
    '''Close the MongoDB (if it's open).'''

    client = g.pop('client', None)

    if client is not None:
        client.close()


def add_db_syncs_and_teardowns(app):
    '''Enable apps to resync with CSVs and close the db connection.
    
    app.teardown_appcontext() tells Flask to call the close_db
    functions when cleaning up after returning the response.

    '''

    app.cli.add_command(csv_sync_command)
    app.teardown_appcontext(close_dbf)
    app.teardown_appcontext(close_dbm)


def db_csv_sync():
    '''Resync databases with CSV files.'''

    # index

    # haveyouseenx
    backlog_path = os.path.join(
        os.getcwd(),
        'data',
        'haveyouseenx',
        'haveyouseenx_annuitydew.csv'
    )
    annuitydew = Backlog('annuitydew')
    annuitydew.from_csv(backlog_path)
    annuitydew.to_mongo()


@click.command('csv-sync')
@with_appcontext
def csv_sync_command():
    db_csv_sync()
    click.echo('Resynced MongoDB and Firestore with CSVs!')


class Backlog:
    def __init__(self, backlog_owner):
        self.backlog_owner = backlog_owner
        self.backlog_dict = {}

    def add_game(self, backlog_game):
        self.backlog_dict[backlog_game._id] = backlog_game

    def remove_game(self, _id):
        del self.backlog_dict[_id]

    def from_csv(self, backlog_path):
        with open(backlog_path, encoding='latin1') as backlog_csv:
            eastern = pytz.timezone('US/Eastern')
            backlog_reader = csv.reader(backlog_csv)
            # skip header row
            next(backlog_reader)
            for row in backlog_reader:
                # convert date strings to datetime objects and ints to int
                if row[7] != '':
                    row[7] = int(row[7])
                if row[8] != '':
                    row[8] = int(row[8])
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
                    _id=row[0],
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
                _id=index,
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
        db = get_dbf()
        doc_ref = db.collection('backlogs').document(self.backlog_owner)
        for _id, backlog_game in self.backlog_dict.items():
            doc_ref.collection('games').document(_id).set(
                backlog_game.to_dict()
            )

    def to_mongo(self):
        dbm, client = get_dbm()
        dbm.annuitydew.insert_many([backlog_game.to_dict() for _id, backlog_game in self.backlog_dict.items()])
        # create index
        dbm.annuitydew.create_index([
            ("game_title", pymongo.TEXT),
            ("sub_title", pymongo.TEXT)
        ])

    def print_backlog(self):
        print(f'Backlog(backlog_owner={self.backlog_owner})')
        for _id, backlog_game in self.backlog_dict.items():
            print(f'{_id}: {backlog_game.game_title}')


class BacklogGame:
    def __init__(self, _id, game_title, game_system, genre,
                 now_playing, game_status, playtime_calc,
                 game_hours=0, game_minutes=0, sub_title=None,
                 add_date=None, start_date=None, beat_date=None,
                 complete_date=None, game_notes=None):
        self._id = _id
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
            f'_id={self._id}, ' +
            str(type(self._id)) + "\n    " +
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
