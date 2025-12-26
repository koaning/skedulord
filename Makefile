.PHONY: lint install develop test check clean reset reset-big pypi \
	demo-reset demo-seed demo-run demo-web demo-clean demo-install demo-ui-build demo-check

lint:
	ruff check skedulord tests

install:
	@if [ ! -d ".venv" ]; then uv venv .venv; fi
	uv pip install -e ".[dev]"
	cd webapp && npm install

develop: install
	uv pip install -e ".[dev]"

test:
	uv run pytest tests

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

demo-reset:
	uv run python -m skedulord wipe disk --really --yes


demo-seed:
	uv run python -m skedulord.demo_seed


demo-run: demo-reset demo-seed demo-ui-build
	uv run python -m skedulord serve --reload


demo-web:
	cd webapp && npm install && npm run dev


demo-ui-build:
	cd webapp && npm install && npm run build


demo-clean:
	uv run python -m skedulord wipe disk --really --yes


demo-install:
	uv pip install -e ".[dev]"


demo-check:
	uv run python -m skedulord history --n 5
