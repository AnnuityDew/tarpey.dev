# import native Python packages

# import third party packages
import pandas
import seaborn
from starlette.routing import Route
from starlette.templating import Jinja2Templates


# templates
templates = Jinja2Templates(directory='templates')


# home page
async def homepage(request):
    # generate color palette using Seaborn for the main site buttons
    app_colors = main_color_palette()

    return templates.TemplateResponse(
        'index/index.html',
        context={
            'request': request,
        }
    )


def colors(request):
    return templates.TemplateResponse(
        'index/colors.html',
        context={
            'request': request,
        }
    )


def links(request):
    return templates.TemplateResponse(
        'index/links.html',
        context={
            'request': request,
        }
    )


def games(request):
    return templates.TemplateResponse(
        'index/games.html',
        context={
            'request': request,
        }
    )


def main_color_palette():
    # obtain circular palette of hex colors for the main page.
    # h = starting hue
    # l = lightness
    # s = saturation
    hex_color_list = seaborn.hls_palette(7, h=.75, l=.3, s=.7).as_hex()
    # hex_color_list = seaborn.color_palette("cubehelix", 7).as_hex()

    # add the rest of the html style formatting string to each
    hex_color_list = ["color:ffffff; background-color:" + color for color in hex_color_list]
    return hex_color_list


routes = [
    Route("/colors", colors, name="colors"),
    Route("/links", links, name="links"),
    Route("/games", games, name="games"),
]
