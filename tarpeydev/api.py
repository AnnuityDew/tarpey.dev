# import native Python packages
import random

# import third party packages
from flask import Blueprint, jsonify, request

# import local stuff
from tarpeydev.db import get_dbmr
from tarpeydev.users import login_required


api_bp = Blueprint('api', __name__, url_prefix='/api')


@api_bp.route('/index/random-quote', methods=['GET'])
def random_quote():
    client = get_dbmr()
    db = client.quotes
    quote_count = db.quotes.estimated_document_count()
    quote_id = str(random.randint(1, quote_count))
    quote = db.quotes.find_one({"_id": quote_id})
    return quote


@api_bp.route('/haveyouseenx/search', methods=['GET'])
def search(search_term=None, front_end=False):
    if search_term is None:
        search_term = request.args.get('query')
    if search_term is None:
        error = "You can't call this URL without a query!"
        return error, 569
    client = get_dbmr()
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
    if front_end is True:
        return results
    else:
        return jsonify(results), 200


@api_bp.route('/users', methods=['POST'])
@login_required
def create():
    return


@api_bp.route('/users/<username>', methods=['GET'])
@login_required
def read(username):
    client = get_dbmr()
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
