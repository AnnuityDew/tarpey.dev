# import native Python packages

# import third party packages
from flask import Blueprint, jsonify, request

# import local stuff
from tarpeydev.admin import login_required
from tarpeydev.db import get_dbb, get_users


api_bp = Blueprint('api', __name__, url_prefix='/api')


@api_bp.route('/haveyouseenx/search', methods=['GET'])
def search(search_term=None, front_end=False):
    if search_term is None:
        search_term = request.args.get('query')
    if search_term is None:
        error = "You can't call this URL without a query!"
        return error, 569
    dbb, client = get_dbb()
    # return all results if no search_term
    if search_term == '':
        results = list(dbb.annuitydew.find())
    else:
        results = list(dbb.annuitydew.find(
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
    dbu, client = get_users()
    user = dbu.users.find_one({"_id": username})
    if user is not None:
        return user
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
