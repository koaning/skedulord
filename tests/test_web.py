import pytest

from skedulord.web.app import create_app


@pytest.fixture
def test_app():
    return create_app().test_client()


def test_mirror(test_app):
    resp = test_app.post("/mirror", json={"foo": "bar"})
    print(resp)
    assert resp.get_json()["foo"] == "bar"
