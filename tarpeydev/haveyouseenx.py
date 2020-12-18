# import native Python packages
import json

# import third party packages
from starlette.routing import Route
from starlette.templating import Jinja2Templates

# import local stuff
from api import haveyouseenx as hysx


# templates
templates = Jinja2Templates(directory='templates')


async def home(request):
    return templates.TemplateResponse(
        'haveyouseenx/home.html',
        context={
            'request': request,
        }
    )


async def results(request):
    # run search
    results = hysx.search(request.query_params['query'])
    return templates.TemplateResponse(
        'haveyouseenx/results.html',
        context={
            'request': request,
            'search_term': request.query_params['query'],
            'results': results,
        }
    )


routes = [
    Route("/", endpoint=home, name="haveyouseenx"),
    Route("/results", endpoint=results, name="search_results"),
]
