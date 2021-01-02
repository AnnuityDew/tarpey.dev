# import native Python packages

# import third party packages
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

# import custom local stuff
from instance.config import GCP_FILE
from tarpeydev import (
    index,
    autobracket,
    ddr,
    haveyouseenx,
    mildredleague,
    timecapsule,
    users,
)
from api.index import index_api
from api.haveyouseenx import hysx_api
from api.mildredleague import ml_api
from api.users import users_api

# GCP debugger
try:
    import googleclouddebugger
    googleclouddebugger.enable(
        breakpoint_enable_canary=False,
        service_account_json_file=GCP_FILE,
    )
except ImportError:
    pass


def create_fastapi_app():
    # create the root and API FastAPI apps
    view_app = FastAPI(
        title="tarpey.dev",
        description="Mike Tarpey's app sandbox.",
        docs_url=None,
        redoc_url=None,
    )

    api_app = FastAPI(
        title="tarpey.dev API",
        description="API for Mike Tarpey's app sandbox.",
        servers=[
            {"url": "http://127.0.0.1:8000/api", "description": "Testing environment."},
            {"url": "https://dev.tarpey.dev/api", "description": "Staging environment."},
            {"url": "https://tarpey.dev/api", "description": "Production environment"},
        ],
    )

    # config stuff
    view_app.mount("/static", app=StaticFiles(directory='static'), name="static")

    # include subrouters of views
    view_app.include_router(index.index_views)
    view_app.include_router(autobracket.autobracket_views)
    view_app.include_router(ddr.ddr_views)
    view_app.include_router(haveyouseenx.hysx_views)
    view_app.include_router(mildredleague.ml_views)
    view_app.include_router(timecapsule.tc_views)
    view_app.include_router(timecapsule.tcd_views)
    view_app.include_router(users.user_views)

    # include subrouters of the FastAPI app
    api_app.include_router(index_api)
    api_app.include_router(hysx_api)
    api_app.include_router(ml_api)
    api_app.include_router(users_api)

    # stitch it all together
    view_app.mount("/api", app=api_app, name="api_app")

    return view_app


# entrypoint!
app = create_fastapi_app()
