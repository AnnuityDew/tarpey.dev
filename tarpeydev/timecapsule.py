# import native Python packages

# import third party packages
from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates


# router and templates
tc_views = APIRouter(prefix="/timecapsule")
tcd_views = APIRouter(prefix="/timecapsuledeep")
templates = Jinja2Templates(directory='templates')


@tc_views.get('/{template_id}')
def timecapsule(request: Request, template_id: str):
    template_url = f'timecapsule/{template_id}.html'
    return templates.TemplateResponse(
        template_url,
        context={'request': request},
    )


@tcd_views.get('/{template_id}')
def timecapsuledeep(request: Request, template_id: str):
    template_url = f'timecapsuledeep/{template_id}.html'
    return templates.TemplateResponse(
        template_url,
        context={'request': request},
    )
