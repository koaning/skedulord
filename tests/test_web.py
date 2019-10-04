import pytest

from skedulord.web.app import create_app


@pytest.fixture
def test_app():
    return create_app().test_client()


def test_mirror(test_app):
    resp = test_app.post("/mirror", json={"foo": "bar"})
    assert resp.get_json()["foo"] == "bar"


def test_index(test_app):
    resp = test_app.get("/")
    assert resp.status == 200


def test_logo(test_app):
    resp = test_app.get("/logo")
    assert resp.status == 200
