# import native Python packages

# import third party packages
from fastapi import FastAPI
from starlette.applications import Starlette
from starlette.routing import Route, Mount
from starlette.staticfiles import StaticFiles


# import custom local stuff
from instance.config import GCP_FILE
from tarpeydev import (
    index, autobracket, ddr
)
from api.index import index_api
from api.haveyouseenx import hysx_api
from api.mildredleague import ml_api

# GCP debugger
try:
    import googleclouddebugger
    googleclouddebugger.enable(
        breakpoint_enable_canary=True,
        service_account_json_file=GCP_FILE,
    )
except ImportError:
    pass


def create_starlette_app():
    # create the main FastAPI app
    fastapi_app = FastAPI()

    # include subrouters on the FastAPI app
    fastapi_app.include_router(index_api)
    fastapi_app.include_router(hysx_api)
    fastapi_app.include_router(ml_api)

    # starlette routes
    routes = [
        Route("/", endpoint=index.homepage),
        index.routes[0],
        index.routes[1],
        index.routes[2],
        Mount("/autobracket", routes=autobracket.routes),
        # Mount("/db", routes=db.routes),
        Mount("/ddr", routes=ddr.routes),
        # Mount("/haveyouseenx", routes=haveyouseenx.routes),
        # Mount("/mildredleague", routes=mildredleague.routes),
        # Mount("/timecapsule", routes=timecapsule.routes),
        Mount("/api", app=fastapi_app, name='fastapi_app'),
        Mount('/static', app=StaticFiles(directory='static'), name='static')
    ]

    return Starlette(debug=True, routes=routes)


# entrypoint!
app = create_starlette_app()
