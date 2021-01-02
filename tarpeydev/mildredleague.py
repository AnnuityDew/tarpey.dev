# import native Python packages

# import third party packages
from fastapi import APIRouter, Request, Depends, Path
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates


# import custom local stuff
from api.mildredleague import (
    matchup_heatmap_fig,
    all_time_ranking_fig,
    win_total_fig,
    get_season_notes,
    get_season_games,
    season_boxplot_fig,
    season_table,
    seed_sim,
)
from api.users import (
    UserOut,
    oauth2_scheme,
)


# router and templates
ml_views = APIRouter(prefix="/mildredleague", tags=["testable_view"])
templates = Jinja2Templates(directory='templates')


@ml_views.get("/game-admin", response_class=HTMLResponse)
def game_admin(
    request: Request,
    user: UserOut = Depends(oauth2_scheme),
):
    return templates.TemplateResponse(
        'mildredleague/games.html',
        context={'request': request},
    )


@ml_views.get("/note-admin", response_class=HTMLResponse)
def note_admin(
    request: Request,
    user: UserOut = Depends(oauth2_scheme),
):
    return templates.TemplateResponse(
        'mildredleague/notes.html',
        context={'request': request},
    )


@ml_views.get("/", response_class=HTMLResponse)
def mildredleague(request: Request):
    return templates.TemplateResponse(
        'mildredleague/home.html',
        context={'request': request},
    )


@ml_views.get("/all-time", response_class=HTMLResponse)
def all_time(
    request: Request,
):

    return templates.TemplateResponse(
        'mildredleague/alltime.html',
        context={
            'request': request,
        }
    )


@ml_views.get("/rules", response_class=HTMLResponse)
def rules(request: Request):
    return templates.TemplateResponse(
        'mildredleague/rules.html',
        context={
            'request': request,
        }
    )


@ml_views.get("/{season}", response_class=HTMLResponse)
def season_page(
    request: Request,
    season: int = Path(..., ge=2013, le=2020),
    notes_data=Depends(get_season_notes),
):

    return templates.TemplateResponse(
        'mildredleague/season.html',
        context={
            'request': request,
            'season': season,
            'notes_data': notes_data,
        }
    )


@ml_views.get("/sim/{season}", response_class=HTMLResponse)
def simulation(
    request: Request,
    season: int = Path(..., ge=2013, le=2020),
    playoff_table=Depends(seed_sim),
):
    if True:
        return RedirectResponse(request.url_for('mildredleague.season_page', season=season))
    elif season != 2020:
        return "You can't simulate this season.", 404
    else:
        return templates.TemplateResponse(
            'mildredleague/sim.html',
            context={
                'request': request,
                'season': season,
                'playoff_table': playoff_table,
            }
        )
