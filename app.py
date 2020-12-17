# import native Python packages
import os

# import third party packages
from fastapi import FastAPI, Request
from flask import Flask
from starlette.applications import Starlette
from starlette.routing import Route, Mount
from starlette.staticfiles import StaticFiles


# import custom local stuff
from instance.config import GCP_FILE
from tarpeydev import (
    index
)
from api.index import index_api
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

    # include subrouters on the FastAPI app
    fastapi_app.include_router(index_api)
    fastapi_app.include_router(ml_api)

    # starlette routes
    routes = [
        Route("/", endpoint=index.homepage),
        index.routes[0],
        index.routes[1],
        index.routes[2],
        # Mount("/autobracket", routes=autobracket.routes),
        # Mount("/db", routes=db.routes),
        # Mount("/ddr", routes=ddr.routes),
        # Mount("/haveyouseenx", routes=haveyouseenx.routes),
        # Mount("/mildredleague", routes=mildredleague.routes),
        # Mount("/timecapsule", routes=timecapsule.routes),
        Mount("/api", app=fastapi_app, name='fastapi_app'),
        Mount('/static', app=StaticFiles(directory='static'), name='static')
    ]

    return Starlette(debug=True, routes=routes)

# entrypoint!
app = create_starlette_app()
