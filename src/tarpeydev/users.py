# import native Python packages
import os

# import third party packages
from fastapi import APIRouter, Request, Depends, Response
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

# import custom local stuff
from src.api.users import (
    login_for_access_token, create_user, UserOut, Token
)


# router and templates
user_views = APIRouter(prefix="/users")
templates = Jinja2Templates(directory='templates')


@user_views.get('/register', response_class=HTMLResponse, tags=["simple_view"])
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
                'message': 'Registration failed! Try again.'
            },
        )


@user_views.get('/login', response_class=HTMLResponse, tags=["simple_view"])
def login(request: Request):
    return templates.TemplateResponse(
        'users/login.html',
        context={'request': request},
    )


@user_views.post('/auth', response_class=HTMLResponse)
def auth(
    request: Request,
    response: Response,
    token: Token = Depends(login_for_access_token),
):
    if token:
        token = token.get('access_token')
        response = templates.TemplateResponse(
            'users/login.html',
            context={
                'request': request,
                'message': 'Login successful!',
            },
        )

        # secure cookie if in production
        if os.getenv('SITE_ENV') == 'prod':
            SET_SECURE = True
        else:
            SET_SECURE = False

        response.set_cookie(
            key='Authorization',
            value=token,
            max_age=1800,
            expires=1800,
            secure=SET_SECURE,
            httponly=True,
            samesite='lax',
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


@user_views.get('/logout', response_class=HTMLResponse, tags=["simple_view"])
def logout(request: Request):
    response = RedirectResponse(request.url_for('homepage'))
    response.delete_cookie("Authorization")
    return response
