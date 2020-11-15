import functools

from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for
)

from werkzeug.security import check_password_hash, generate_password_hash

from tarpeydev.db import get_dbmr, get_dbmw

bp = Blueprint('users', __name__, url_prefix='/users')


@bp.route('/register', methods=('GET', 'POST'))
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        client = get_dbmw()
        db = client.users
        error = None

        if not username:
            error = 'Username is required.'
        elif not password:
            error = 'Password is required.'
        elif not username.isalnum():
            error = 'Username must be alphanumeric.'
        elif not password.isalnum():
            error = 'Password must be alphanumeric.'
        elif (username != 'matt') & (username != 'annuitydew'):
            error = 'Registration is currently closed!'
        else:
            user = db.users.find_one({"_id": username})
            if user is not None:
                error = f'User {username} is already registered.'

        if error is None:
            db.users.insert_one({
                "_id": username,
                "password": generate_password_hash(password)
            })
            return redirect(url_for('users.login'))

        flash(error)

    return render_template('users/register.html')


@bp.route('/', methods=('GET', 'POST'))
@bp.route('/login', methods=('GET', 'POST'))
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        client = get_dbmr()
        db = client.users
        error = None
        user = db.users.find_one({"_id": username})

        if not username.isalnum():
            error = 'Username must be alphanumeric.'
        elif not password.isalnum():
            error = 'Password must be alphanumeric.'
        elif user is None:
            error = 'Incorrect username.'
        elif not check_password_hash(user.get('password'), password):
            error = 'Incorrect password.'

        if error is None:
            session.clear()
            session['user_id'] = user.get('_id')
            return redirect(url_for('index.index'))

        flash(error)

    return render_template('users/login.html')


@bp.before_app_request
def load_logged_in_user():
    user_id = session.get('user_id')

    if user_id is None:
        g.user = None
    else:
        client = get_dbmr()
        db = client.users
        g.user = db.users.find_one({"_id": user_id})


@bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index.index'))


def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for('users.login'))

        return view(**kwargs)

    return wrapped_view
