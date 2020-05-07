# import native Python packages
import os

# import third party packages
from flask import Flask


def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY=os.environ['SECRET_KEY'],
        # DATABASE=os.path.join(app.instance_path, 'flaskr.sqlite'),
    )

    if test_config is None:
        # load the instance config, if it exists, when not testing
        app.config.from_pyfile('config.py', silent=True)
    else:
        # load the test config if passed in
        app.config.from_mapping(test_config)

    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass
    
    # import apps
    from . import index
    from . import haveyouseenx
    from . import autobracket
    from . import timecapsule

    # register apps
    app.register_blueprint(index.index_bp)
    app.register_blueprint(haveyouseenx.hysx_bp)
    app.register_blueprint(autobracket.autobracket_bp)
    app.register_blueprint(timecapsule.timecapsule_bp)
    # app.register_blueprint(ddr.ddr_bp)
    # app.register_blueprint(health.health_bp)

    # import and register errors
    # from . import errors
    # app.register_error_handler(400, handle_bad_request)

    return app

app = create_app()
