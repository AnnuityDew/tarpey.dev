# import native Python packages
import os

# import third party packages
from fastapi import FastAPI, APIRouter, Request
from fastapi.middleware.wsgi import WSGIMiddleware
from flask import Flask

# import custom local stuff
from api.mildredleague import ml_api
from instance.config import GCP_FILE


def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__, instance_relative_config=True)

    if test_config is None:
        # load the instance config, if it exists, when not testing
        app.config.from_pyfile('config.py')
    else:
        # load the test config if passed in
        app.config.from_mapping(test_config)

    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    # import db
    from tarpeydev import db
    # make sure app can close the connection to db
    db.add_db_syncs_and_teardowns(app)

    # import apps
    from tarpeydev import api
    from tarpeydev import autobracket
    from tarpeydev import ddr
    from tarpeydev import haveyouseenx
    from tarpeydev import index
    from tarpeydev import mildredleague
    from tarpeydev import swagger
    from tarpeydev import timecapsule
    from tarpeydev import users

    # register apps
    app.register_blueprint(api.api_bp)
    app.register_blueprint(autobracket.bp)
    app.register_blueprint(ddr.ddr_bp)
    app.register_blueprint(haveyouseenx.hysx_bp)
    app.register_blueprint(index.index_bp)
    app.register_blueprint(mildredleague.ml_bp)
    app.register_blueprint(swagger.swag_bp)
    app.register_blueprint(timecapsule.timecapsule_bp)
    app.register_blueprint(users.bp)

    # import and register errors
    # from . import errors
    # app.register_error_handler(400, handle_bad_request)

    return app


# GCP debugger
try:
    import googleclouddebugger
    googleclouddebugger.enable(
        breakpoint_enable_canary=True,
        service_account_json_file=GCP_FILE,
    )
except ImportError:
    pass

# flag to determine whether FastAPI or Flask is the main app
use_fastapi = True

# turn on FastAPI and mount flask at the hip
if use_fastapi is True:
    # create the main FastAPI and Flask apps
    fastapi_app = FastAPI()
    flask_app = create_app()

    # super meta stuff at the fastapi_app root
    @fastapi_app.get("/app")
    def read_main(request: Request):
        return {"message": "Hello World", "root_path": request.scope.get("root_path")}

    # meta stuff at the API root
    @fastapi_app.get('/url-list')
    def get_all_urls():
        url_list = [
            {'path': route.path, 'name': route.name}
            for route in fastapi_app.routes
        ]
        return url_list

    # api path router
    api_path = APIRouter(
        prefix="/api",
    )

    # include subrouters on the api_path
    api_path.include_router(ml_api)

    # include api_path on the FastAPI app
    fastapi_app.include_router(api_path)

    # mount the flask app on FastAPI app
    fastapi_app.mount(
        path="",
        app=WSGIMiddleware(flask_app),
        name='flask_app',
        )

else:
    # ...or just use Flask
    app = create_app()

    if __name__ == '__main__':
        if os.environ['FLASK_ENV'] == 'development':
            app.run(debug=True)
