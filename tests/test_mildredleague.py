# import native Python packages

# import third party packages
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.testclient import TestClient

# import custom local stuff
from .api.mildredleague import ml_api
from .tarpeydev.mildredleague import ml_views

# create test app and client
test_app = FastAPI()
test_api_app = FastAPI()
test_app.mount("/static", app=StaticFiles(directory='static'), name="static")
test_app.include_router(ml_views)
test_api_app.include_router(ml_api)

client = TestClient(test_app)


def test_all_get_urls():
    # probably need to test URLs individually. X_X
    testable_urls = [
        {'tags': route.__dict__.get('tags'), 'path': route.path, 'method': route.methods}
        for route in app.routes
        if route.__dict__.get('tags') and route.__dict__.get('methods') == {'GET'}
    ]
    print(testable_urls)
    print(PS2DDR.__dict__)
    # get request on each view
    response_list = [
        client.get(url.get('path')) for url in testable_urls
    ]
    
    print(response_list)
    assert all(response.status_code == 200 for response in response_list)
