# import native Python packages

# import third party packages
from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

# import local stuff
from src.api.haveyouseenx import (
    count_by_status, playtime, search, system_treemap
)
from src.api.users import (
    UserOut,
    oauth2_scheme,
)


# router and templates
hysx_views = APIRouter(prefix="/haveyouseenx")
templates = Jinja2Templates(directory='templates')


@hysx_views.get("/", response_class=HTMLResponse, name="haveyouseenx", tags=["simple_view"])
async def home(
    request: Request,
    stats=Depends(count_by_status),
    hours=Depends(playtime),
):
    return templates.TemplateResponse(
        'haveyouseenx/home.html',
        context={
            'request': request,
            'stats': stats,
            'playtime': hours,
        }
    )


@hysx_views.get("/results", response_class=HTMLResponse, tags=["query_view"])
async def search_results(
    request: Request,
):
    return templates.TemplateResponse(
        'haveyouseenx/results.html',
        context={
            'request': request,
            'search_term': request.query_params['q'],
        }
    )


@hysx_views.get("/game-admin", response_class=HTMLResponse)
def game_admin(
    request: Request,
    user: UserOut = Depends(oauth2_scheme),
):
    return templates.TemplateResponse(
        'haveyouseenx/game-admin.html',
        context={'request': request},
    )
