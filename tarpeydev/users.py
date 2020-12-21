# import native Python packages
import functools

# import third party packages
from fastapi import APIRouter, Request, Depends, Response
from fastapi.encoders import jsonable_encoder
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates


# import custom local stuff
from api.users import (
    login_for_access_token, create_user, UserOut, Token
)


# router and templates
user_views = APIRouter(prefix="/users")
templates = Jinja2Templates(directory='templates')


@user_views.get('/register', response_class=HTMLResponse)
def register(request: Request):
    return templates.TemplateResponse(
        'users/register.html',
        context={'request': request},
    )


@user_views.post('/register-result', response_class=HTMLResponse)
def register_result(
    request: Request,
    user: UserOut = Depends(create_user),
):
    if user:
        return templates.TemplateResponse(
            'users/login.html',
            context={
                'request': request,
                'message': 'Registration successful! Please login.'
            },
        )
    else:
        return templates.TemplateResponse(
            'users/register.html',
            context={
                'request': request,
                'message': 'Registration failed!'
            },
        )


@user_views.get('/login', response_class=HTMLResponse)
def login(request: Request):
    return templates.TemplateResponse(
        'users/login.html',
        context={'request': request},
    )


@user_views.post('/login-result', response_class=HTMLResponse)
def login_result(
    request: Request,
    response: Response,
    token: Token = Depends(login_for_access_token),
):
    if token:
        token = jsonable_encoder(token)
        response = templates.TemplateResponse(
            'users/login.html',
            context={
                'request': request,
                'message': 'Login successful!',
            },
        )
        response.set_cookie(
            key="Authorization",
            value=f"Bearer {token['access_token']}",
            max_age=1234,
            expires=1234,
            secure=True,
            httponly=True,
        )
        return response
    else:
        return templates.TemplateResponse(
            'users/login.html',
            context={
                'request': request,
                'message': 'Login error!',
            },
        )


@user_views.get('/logout', response_class=HTMLResponse)
def logout(request: Request):
    response = RedirectResponse(request.url_for('homepage'))
    response.delete_cookie("Authorization")
    return response


def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if user is None:
            return RedirectResponse(request.url_for('login'))

        return view(**kwargs)

    return wrapped_view
