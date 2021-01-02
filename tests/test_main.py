# import native Python packages

# import third party packages
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.testclient import TestClient

# import custom local stuff
from src.main import create_fastapi_app

# create test app and client
app = create_fastapi_app()
client = TestClient(app)


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
