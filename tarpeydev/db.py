# import native Python packages
import click
import csv
import datetime
import os

# import third party packages
from flask import current_app, g
from flask.cli import with_appcontext
from google.cloud import firestore
import pandas
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


def get_dbmr():
    '''Retrieve the MongoDB reader.'''

    if 'client' not in g:
        g.client = MongoClient(current_app.config['MONGO_READER'])

    return g.client


def get_dbmw():
    '''Retrieve the MongoDB writer.'''

    if 'client' not in g:
        g.client = MongoClient(current_app.config['MONGO_WRITER'])

    return g.client


def get_dbma():
    '''Retrieve the MongoDB admin.'''

    if 'client' not in g:
        g.client = MongoClient(current_app.config['MONGO_ADMIN'])

    return g.client


def get_users():
    '''Retrieve the MongoDB users.'''

    if 'dbu' not in g:
        g.client = MongoClient(current_app.config['USERS_KEY'])
        g.dbu = g.client.users

    return g.dbu, g.client


def close_mongo(e=None):
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
    app.cli.add_command(pandas_transformations_command)
    app.teardown_appcontext(close_dbf)
    app.teardown_appcontext(close_mongo)


@click.command('csv-sync')
@with_appcontext
def csv_sync_command():
    db_csv_sync()
    click.echo('Resynced MongoDB and Firestore with CSVs!')


@click.command('chart-update')
@with_appcontext
def pandas_transformations_command():
    pandas_transformations()
    click.echo('Reran data transformations for charts!')


def db_csv_sync():
    '''Resync databases with CSV files.'''

    # index quotes
    quotes_path = os.path.join(
        os.getcwd(),
        'data',
        'index',
        'index_quotes.csv'
    )
    data_list = list(csv.reader(open(quotes_path)))
    instances = [Quote(data_list[0], i) for i in data_list[1:]]

    client = get_dbma()
    db = client.quotes
    doc_list = [quote.to_dict() for quote in instances]
    if list(db.quotes.find()) == doc_list:
        print("All quotes are already synced!")
    elif not list(db.quotes.find()):
        db.quotes.insert_many(doc_list)
        print("Bulk insert complete!")
    else:
        for doc in doc_list:
            try:
                db.quotes.insert_one(doc)
                print("Inserted " + doc.get("_id") + ".")
            except pymongo.errors.DuplicateKeyError:
                db.quotes.replace_one({"_id": doc.get("_id")}, doc)
                print("Replaced " + doc.get("_id") + ".")

    # create index
    db.quotes.create_index([
        ("quote_text", pymongo.TEXT),
        ("quote_origin", pymongo.TEXT)
    ])

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

    # mildredleague
    games_path = os.path.join(
        os.getcwd(),
        'data',
        'mildredleague',
        'mlallgames.csv'
    )
    teams_path = os.path.join(
        os.getcwd(),
        'data',
        'mildredleague',
        'mlallteams.csv'
    )
    season_data = MildredLeagueSeason(2020)
    season_data.games_from_csv(games_path)
    season_data.teams_from_csv(teams_path)
    season_data.games_to_mongo()
    season_data.teams_to_mongo()


def pandas_transformations():
    seasons = [2013, 2014, 2015, 2016, 2017, 2018, 2019]
    for season in seasons:
        season_boxplot_transform(season, against=True)
        season_boxplot_transform(season, against=False)


def season_boxplot_transform(season, against=True):
    # read season data from api
    season_df = pandas.read_json(api.season_data(season))
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
        score_df = season_df[['a_nick', 'a_score_norm']].rename(
            columns={'a_nick': 'name', 'a_score_norm': 'score'},
        ).append(
            season_df[['h_nick', 'h_score_norm']].rename(
                columns={'h_nick': 'name', 'h_score_norm': 'score'},
            ),
            ignore_index=True,
        )
        title_label = '(Points For)'
    # this code runs to analyze Points Against.
    if against is True:
        score_df = season_df[['a_nick', 'h_score_norm']].rename(
            columns={'a_nick': 'name', 'h_score_norm': 'score'},
        ).append(
            season_df[['h_nick', 'a_score_norm']].rename(
                columns={'h_nick': 'name', 'a_score_norm': 'score'},
            ),
            ignore_index=True,
        )
        title_label = '(Points Against)'
    # let's sort by playoff rank instead
    # read season file, but we only need nick_name, year, and playoff_rank
    ranking_df = pandas.read_json(
        api.all_teams_data(),
    )[['nick_name', 'year', 'playoff_rank']]
    # merge this (filtered by year) into score_df so we can sort values
    score_df = score_df.merge(
        ranking_df.loc[ranking_df.year == int(year), ['nick_name', 'playoff_rank']],
        left_on=['name'],
        right_on=['nick_name'],
        how='left',
    ).sort_values(
        by='playoff_rank', ascending=True,
    )

    # convert back to json for writing to Mongo
    data = score_df.to_json()
    return data

    # finally, write back to MongoDB
    client = get_dbmw()
    db = client.mildredleague
    if list(db.charts.find()) == doc_list:
        print(str(season) + "boxplot chart is already synced!")
    elif not list(db.charts.find()):
        db.annuitydew.insert_many(doc_list)
        print("Bulk insert complete!")
    else:
        for _id, backlog_game in self.backlog_dict.items():
            try:
                db.annuitydew.insert_one(backlog_game.to_dict())
                print("Inserted " + _id + ".")
            except pymongo.errors.DuplicateKeyError:
                db.annuitydew.replace_one({"_id": _id}, backlog_game.to_dict())
                print("Replaced " + _id + ".")


class Quote:
    # instantiate from the quotes CSV
    def __init__(self, header, row):
        self.__dict__ = dict(zip(header, row))

    def to_dict(self):
        return self.__dict__

    def print_contents(self):
        print(
            'Quote(' + "\n    " +
            f'_id={self._id}, ' +
            str(type(self._id)) + "\n    " +
            f'quote_text={self.quote_text}, ' +
            str(type(self.quote_text)) + "\n    " +
            f'quote_origin={self.quote_origin}, ' +
            str(type(self.quote_origin)) + "\n    " +
            ')'
        )


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
            backlog_reader = csv.reader(backlog_csv)
            # skip header row
            next(backlog_reader)
            for row in backlog_reader:
                # convert date strings to datetime objects and ints to int
                ints = [7, 8]
                dates = [10, 11, 12, 13]
                for column in ints:
                    if row[column] != '':
                        row[column] = int(row[column])
                for column in dates:
                    if row[column] != '':
                        row[column] = datetime.datetime.strptime(row[column], '%m/%d/%y').replace(hour=16)
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
        # convert strings to dates
        for index, row in backlog_df.iterrows():
            # convert date strings to Python datetime objects
            if row.add_date is not None:
                row.add_date = datetime.datetime.strptime(row.add_date, '%m/%d/%y').replace(hour=16)
            if row.start_date is not None:
                row.start_date = datetime.datetime.strptime(row.start_date, '%m/%d/%y').replace(hour=16)
            if row.beat_date is not None:
                row.beat_date = datetime.datetime.strptime(row.beat_date, '%m/%d/%y').replace(hour=16)
            if row.complete_date is not None:
                row.complete_date = datetime.datetime.strptime(row.complete_date, '%m/%d/%y').replace(hour=16)
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
        client = get_dbma()
        db = client.backlogs
        doc_list = [backlog_game.to_dict() for _id, backlog_game in self.backlog_dict.items()]
        if list(db.annuitydew.find()) == doc_list:
            print("All backlog games are already synced!")
        elif not list(db.annuitydew.find()):
            db.annuitydew.insert_many(doc_list)
            print("Bulk insert complete!")
        else:
            for _id, backlog_game in self.backlog_dict.items():
                try:
                    db.annuitydew.insert_one(backlog_game.to_dict())
                    print("Inserted " + _id + ".")
                except pymongo.errors.DuplicateKeyError:
                    db.annuitydew.replace_one({"_id": _id}, backlog_game.to_dict())
                    print("Replaced " + _id + ".")

        # create index
        db.annuitydew.create_index([
            ("game_title", pymongo.TEXT),
            ("sub_title", pymongo.TEXT)
        ])

    def print_contents(self):
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

    def print_contents(self):
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


class MildredLeagueSeason:
    def __init__(self, season):
        self.season = season
        self.games_dict = {}
        self.teams_dict = {}

    def add_game(self, ml_game):
        self.games_dict[ml_game._id] = ml_game

    def remove_game(self, _id):
        del self.games_dict[_id]

    def add_team(self, ml_team):
        self.teams_dict[ml_team._id] = ml_team

    def remove_team(self, _id):
        del self.teams_dict[_id]

    def games_from_csv(self, games_path):
        with open(games_path) as games_csv:
            games_reader = csv.reader(games_csv)
            # skip header row
            next(games_reader)
            for row in games_reader:
                # convert floats to float and ints to int
                floats = [5, 10]
                ints = [0, 11, 12, 13, 14]
                for column in floats:
                    if row[column] != '':
                        row[column] = float(row[column])
                for column in ints:
                    if row[column] != '':
                        row[column] = int(row[column])
                # convert empty strings to None
                row = [None if item == '' else item for item in row]
                game = MildredLeagueGame(
                    _id=row[0],
                    away=row[1],
                    a_name=row[2],
                    a_nick=row[3],
                    a_division=row[4],
                    a_score=row[5],
                    home=row[6],
                    h_name=row[7],
                    h_nick=row[8],
                    h_division=row[9],
                    h_score=row[10],
                    week_s=row[11],
                    week_e=row[12],
                    season=row[13],
                    playoff=row[14],
                )
                self.add_game(game)

    def teams_from_csv(self, teams_path):
        with open(teams_path) as teams_csv:
            teams_reader = csv.reader(teams_csv)
            # skip header row
            next(teams_reader)
            for row in teams_reader:
                # convert ints to int
                ints = [0, 4, 5, 6]
                for column in ints:
                    if row[column] != '':
                        row[column] = int(row[column])
                # convert empty strings to None
                row = [None if item == '' else item for item in row]
                team = MildredLeagueTeam(
                    _id=row[0],
                    team_name=row[1],
                    full_name=row[2],
                    nick_name=row[3],
                    season=row[4],
                    playoff_rank=row[5],
                    active=row[6],
                )
                self.add_team(team)

    def games_to_mongo(self):
        client = get_dbma()
        db = client.mildredleague
        doc_list = [ml_game.to_dict() for _id, ml_game in self.games_dict.items()]
        if list(db.games.find()) == doc_list:
            print("All Mildred League games are already synced!")
        elif not list(db.games.find()):
            db.games.insert_many(doc_list)
            print("Bulk insert complete!")
        else:
            for _id, ml_game in self.games_dict.items():
                try:
                    db.games.insert_one(ml_game.to_dict())
                    print("Inserted " + str(_id) + ".")
                except pymongo.errors.DuplicateKeyError:
                    db.games.replace_one({"_id": _id}, ml_game.to_dict())
                    print("Replaced " + str(_id) + ".")
        # create index
        db.games.create_index([
            ("a_nick", pymongo.TEXT),
            ("h_nick", pymongo.TEXT)
        ])

    def teams_to_mongo(self):
        client = get_dbma()
        db = client.mildredleague
        doc_list = [ml_team.to_dict() for _id, ml_team in self.teams_dict.items()]
        if list(db.teams.find()) == doc_list:
            print("All Mildred League teams are already synced!")
        elif not list(db.teams.find()):
            db.teams.insert_many(doc_list)
            print("Bulk insert complete!")
        else:
            for _id, ml_team in self.teams_dict.items():
                try:
                    db.teams.insert_one(ml_team.to_dict())
                    print("Inserted " + str(_id) + ".")
                except pymongo.errors.DuplicateKeyError:
                    db.teams.replace_one({"_id": _id}, ml_team.to_dict())
                    print("Replaced " + str(_id) + ".")
        # create index
        db.teams.create_index([
            ("nick_name", pymongo.TEXT)
        ])

    def print_contents(self):
        print(f'Season(season={self.season})')
        for _id, ml_game in self.games_dict.items():
            print(f'{_id}')


class MildredLeagueGame:
    def __init__(self, _id, away, a_name, a_nick, a_division,
                 a_score, home, h_name, h_nick, h_division,
                 h_score, week_s, week_e, season, playoff):
        self._id = _id
        self.away = away
        self.a_name = a_name
        self.a_nick = a_nick
        self.a_division = a_division
        self.a_score = a_score
        self.home = home
        self.h_name = h_name
        self.h_nick = h_nick
        self.h_division = h_division
        self.h_score = h_score
        self.week_s = week_s
        self.week_e = week_e
        self.season = season
        self.playoff = playoff

    def to_dict(self):
        return self.__dict__

    def print_contents(self):
        print(
            'MildredLeagueGame(' + "\n    " +
            f'_id={self._id}, ' +
            str(type(self._id)) + "\n    " +
            f'away={self.away}, ' +
            str(type(self.away)) + "\n    " +
            f'a_name={self.a_name}, ' +
            str(type(self.a_name)) + "\n    " +
            f'a_nick={self.a_nick}, ' +
            str(type(self.a_nick)) + "\n    " +
            f'a_division={self.a_division}, ' +
            str(type(self.a_division)) + "\n    " +
            f'a_score={self.a_score}, ' +
            str(type(self.a_score)) + "\n    " +
            f'home={self.home}, ' +
            str(type(self.home)) + "\n    " +
            f'h_name={self.h_name}, ' +
            str(type(self.h_name)) + "\n    " +
            f'h_nick={self.h_nick}, ' +
            str(type(self.h_nick)) + "\n    " +
            f'h_division={self.h_division}, ' +
            str(type(self.h_division)) + "\n    " +
            f'h_score={self.h_score}, ' +
            str(type(self.h_score)) + "\n    " +
            f'week_s={self.week_s}, ' +
            str(type(self.week_s)) + "\n    " +
            f'week_e={self.week_e}, ' +
            str(type(self.week_e)) + "\n    " +
            f'season={self.season}, ' +
            str(type(self.season)) + "\n    " +
            f'playoff={self.playoff}, ' +
            str(type(self.playoff)) + "\n" +
            ')'
        )


class MildredLeagueTeam:
    def __init__(self, _id, team_name, full_name, nick_name,
                 season, playoff_rank, active):
        self._id = _id
        self.team_name = team_name
        self.full_name = full_name
        self.nick_name = nick_name
        self.season = season
        self.playoff_rank = playoff_rank
        self.active = active

    def to_dict(self):
        return self.__dict__

    def print_contents(self):
        print(
            'MildredLeagueGame(' + "\n    " +
            f'_id={self._id}, ' +
            str(type(self._id)) + "\n    " +
            f'team_name={self.team_name}, ' +
            str(type(self.team_name)) + "\n    " +
            f'full_name={self.full_name}, ' +
            str(type(self.full_name)) + "\n    " +
            f'nick_name={self.nick_name}, ' +
            str(type(self.nick_name)) + "\n    " +
            f'season={self.season}, ' +
            str(type(self.season)) + "\n    " +
            f'playoff_rank={self.playoff_rank}, ' +
            str(type(self.playoff_rank)) + "\n    " +
            f'active={self.active}, ' +
            str(type(self.active)) + "\n    " +
            ')'
        )
