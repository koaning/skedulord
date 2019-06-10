from click.testing import CliRunner

from skedulord.skedulog import decorate


def test_hello_world():
    runner = CliRunner()
    result = runner.invoke(decorate, ['hello vincent'])
    assert "hello" in result.output
    assert "vincent" in result.output
