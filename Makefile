lint:
	ruff check skedulord tests

install:
	uv pip install -e ".[dev]"

develop: install
	uv pip install -e ".[dev]"

test:
	pytest tests

check: lint test clean

clean:
	rm -rf .pytest_cache
	rm -rf build
	rm -rf dist
	rm -rf .ipynb_checkpoints
	rm -rf notebooks/.ipynb_checkpoints
	rm -rf skedulord.egg-info

reset:
	python -m skedulord wipe disk --really --yes
	python -m skedulord wipe schedule --really --yes
	python -m skedulord run pyjob "python jobs/pyjob.py" --retry 1 --wait 0
	python -m skedulord run pyjob "python jobs/pyjob.py" --retry 1 --wait 0
	python -m skedulord run badpyjob "python jobs/badpyjob.py" --retry 3 --wait 0
	python -m skedulord run another-pyjob "python jobs/pyjob.py" --retry 1 --wait 0

reset-big:
	python -m skedulord wipe disk --really --yes
	python -m skedulord wipe schedule --really --yes
	python -m skedulord run pyjob "python jobs/pyjob.py" --retry 1 --wait 0
	python -m skedulord run pyjob "python jobs/pyjob.py" --retry 1 --wait 0
	python -m skedulord run badpyjob "python jobs/badpyjob.py" --retry 3 --wait 0
	python -m skedulord run another-pyjob "python jobs/pyjob.py" --retry 1 --wait 0
	python -m skedulord run pyjob "python jobs/pyjob.py" --retry 1 --wait 0
	python -m skedulord run pyjob "python jobs/pyjob.py" --retry 1 --wait 0
	python -m skedulord run badpyjob "python jobs/badpyjob.py" --retry 3 --wait 1
	python -m skedulord run another-pyjob "python jobs/pyjob.py" --retry 1 --wait 0

pypi:
	rm -rf dist
	uv build
	twine upload dist/*
