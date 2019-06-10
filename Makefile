flake:
	flake8 skedulord
	flake8 tests

install:
	pip install -e ".[dev]"

develop: install
	python setup.py develop

test:
	pytest --cov=skedulord

check: flake test clean

clean:
	rm -rf .pytest_cache
	rm -rf build
	rm -rf dist
	rm -rf scikit_lego.egg-info
	rm -rf .ipynb_checkpoints
	rm -rf notebooks/.ipynb_checkpoints
	rm -rf skedulord.egg-info

build:
	docker build -t pythoncontainer .

test-gitlab:
	gitlab-runner exec docker test