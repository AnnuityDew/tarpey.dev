# import native Python packages

# import third party packages
from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

# import local stuff
from api.haveyouseenx import (
    count_by_status, playtime, search
)


# router and templates
hysx_views = APIRouter(prefix="/haveyouseenx")
templates = Jinja2Templates(directory='templates')


@hysx_views.get("/", response_class=HTMLResponse, name="haveyouseenx")
async def home(request: Request, stats=Depends(count_by_status), hours=Depends(playtime)):
    return templates.TemplateResponse(
        'haveyouseenx/home.html',
        context={
            'request': request,
            'stats': stats,
            'playtime': hours,
        }
    )


@hysx_views.get("/results", response_class=HTMLResponse)
async def search_results(request: Request, q: str, results=Depends(search)):
    return templates.TemplateResponse(
        'haveyouseenx/results.html',
        context={
            'request': request,
            'search_term': request.query_params['q'],
            'results': results,
        }
    )
