# import native Python packages

# import third party packages
from fastapi import FastAPI
from starlette.applications import Starlette
from starlette.routing import Route, Mount
from starlette.staticfiles import StaticFiles


# import custom local stuff
from instance.config import GCP_FILE
from tarpeydev import (
    index, autobracket, ddr, haveyouseenx, mildredleague
)
from api.index import index_api
from api.haveyouseenx import hysx_api
from api.mildredleague import ml_api
from api.users import users_api

# GCP debugger
try:
    import googleclouddebugger
    googleclouddebugger.enable(
        breakpoint_enable_canary=True,
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
    )

    # include subrouters of views
    view_app.include_router(index.index_views)
    view_app.include_router(autobracket.autobracket_views)
    view_app.include_router(ddr.ddr_views)
    view_app.include_router(haveyouseenx.hysx_views)
    view_app.include_router(mildredleague.ml_views)

    # include subrouters of the FastAPI app
    api_app.include_router(index_api)
    api_app.include_router(hysx_api)
    api_app.include_router(ml_api)
    api_app.include_router(users_api)

    # stitch it all together
    view_app.mount("/api", app=api_app, name="api_app")
    view_app.mount("/static", app=StaticFiles(directory="static"), name="static")

    return view_app


# entrypoint!
app = create_fastapi_app()
