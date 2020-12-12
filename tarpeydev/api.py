# import native Python packages
import random

# import third party packages
from flask import Blueprint, jsonify, request

# import local stuff
from tarpeydev.db import get_dbm
from tarpeydev.users import login_required


api_bp = Blueprint('api', __name__, url_prefix='/api')


@api_bp.route('/index/random-quote', methods=['GET'])
def random_quote():
    client = get_dbm()
    db = client.quotes
    quote_count = db.quotes.estimated_document_count()
    quote_id = str(random.randint(1, quote_count))
    quote = db.quotes.find_one({"_id": quote_id})
    return quote


@api_bp.route('/haveyouseenx/all-games', methods=['GET'])
def backlog():
    client = get_dbm()
    db = client.backlogs
    collection = db.annuitydew
    results = list(collection.find())
    return jsonify(results), 200


@api_bp.route('/haveyouseenx/count-by-status', methods=['GET'])
def count_by_status():
    client = get_dbm()
    db = client.backlogs
    collection = db.annuitydew
    results = list(
        collection.aggregate([{
            '$group': {
                '_id': '$game_status',
                'count': {
                    '$sum': 1
                }
            }
        }])
    )
    return jsonify(results), 200


@api_bp.route('/haveyouseenx/playtime', methods=['GET'])
def playtime():
    client = get_dbm()
    db = client.backlogs
    collection = db.annuitydew
    results = list(
        collection.aggregate([{
            '$group': {
                '_id': None,
                'total_hours': {
                    '$sum': '$game_hours'
                },
                'total_minutes': {
                    '$sum': '$game_minutes'
                }
            }
        }])
    )
    # move chunks of 60 minutes into the hours count
    leftover_minutes = results[0].get('total_minutes') % 60
    hours_to_move = (results[0].get('total_minutes') - leftover_minutes) / 60
    results[0]['total_hours'] = results[0]['total_hours'] + hours_to_move
    results[0]['total_minutes'] = leftover_minutes

    return jsonify(results), 200


@api_bp.route('/haveyouseenx/search', methods=['GET'])
def search(search_term=None):
    if search_term is None:
        search_term = request.args.get('query')
    if search_term is None:
        error = "You can't call this URL without a query!"
        return error, 569
    client = get_dbm()
    db = client.backlogs
    # return all results if no search_term
    if search_term == '':
        results = list(db.annuitydew.find())
    else:
        results = list(db.annuitydew.find(
            {
                '$text': {
                    '$search': search_term
                }
            }
        ))
    if request.path.startswith('/api/'):
        return jsonify(results), 200
    else:
        return results


@api_bp.route('/users', methods=['POST'])
@login_required
def create_user():
    return


@api_bp.route('/users/<username>', methods=['GET'])
@login_required
def read(username):
    client = get_dbm()
    db = client.users
    user = db.users.find_one({"_id": username})
    if user is not None:
        return user.get("_id")
    else:
        return "Error!"


@api_bp.route('/users', methods=['POST', 'PUT'])
@login_required
def update():
    return


@api_bp.route('/users', methods=['GET', 'DELETE'])
@login_required
def delete():
    return


def auto_increment_mongo(database, collection):
    '''Retrieve the next _id for a given Mongo collection.'''
    client = get_dbm()
    db = getattr(client, database)
    collection = getattr(db, collection)
    last_id_list = list(
        collection.aggregate([{
            '$group': {
                '_id': None,
                'last_id': {'$max': '$_id'}
            }
        }])
    )
    # if the list is empty, then the next id will be 1
    # otherwise it's the last id + 1
    if not last_id_list:
        next_id = 1
    else:
        next_id = last_id_list[0].get('last_id') + 1

    return next_id
