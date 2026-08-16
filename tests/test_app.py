import pytest
from worm_cat_app import app


@pytest.fixture
def client():
    app.config["TESTING"] = True
    app.config["WTF_CSRF_ENABLED"] = False
    with app.test_client() as client:
        yield client


def test_index_get(client):
    response = client.get("/")
    assert response.status_code == 200
    assert b"WormCat" in response.data


def test_demos_get(client):
    response = client.get("/demos")
    assert response.status_code == 200


def test_404_error(client):
    response = client.get("/non_existent_page_12345")
    assert response.status_code == 404


def test_sunburst_sanitization_valid(client):
    response = client.get("/sunburst?dir=test_run_123")
    assert response.status_code == 302
    assert response.headers["Location"] == "/static/dynamic/test_run_123/sunburst.html"


def test_sunburst_sanitization_invalid(client):
    response = client.get("/sunburst?dir=../../etc/passwd")
    assert response.status_code == 302
    assert ".." not in response.headers["Location"]


def test_sunburst_empty(client):
    response = client.get("/sunburst?dir=")
    assert response.status_code == 404
