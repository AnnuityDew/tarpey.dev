# import native Python packages

# import third party packages
from fastapi.testclient import TestClient

# import custom local stuff
from main import create_fastapi_app


# create test client
app = create_fastapi_app()
client = TestClient(app)


def test_all_urls():
    url_list = [
        {'path': route.path, 'name': route.name}
        for route in app.routes
    ]
    response_list = [client.get(route.path) for route in app.routes]
    assert all(response.status_code == 200 for response in response_list)
