import pytest

from skedulord.web import create_app


@pytest.fixture
def test_app():
    return create_app().test_client()


def test_hello(test_app):
    resp = test_app.get("/hello")
    assert b"hello" in resp.data


def test_mirror(test_app):
    resp = test_app.post("/mirror", json={"foo": "bar"})
    assert resp.get_json()["foo"] == "bar"
