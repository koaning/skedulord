flake:
	flake8 skedulord
	flake8 tests
	flake8 setup.py

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

dev:
	cd skedulord/dashboard && gatsby build
	cp -r skedulord/dashboard/public/* skedulord/web/templates
	cd skedulord/dashboard && gatsby clean
	skedulord serve

reset:
	lord nuke --sure --really
	lord setup --name logger --wait 1 --attempts 3
	lord run pyjob1 "python jobs/badpyjob.py" --wait 1
	lord run pyjob1 "python jobs/badpyjob.py" --wait 1
	lord run pyjob1 "python jobs/pyjob.py" --wait 1
	lord run pyjob2 "python jobs/pyjob.py" --wait 1
	lord run pyjob2 "python jobs/pyjob.py" --wait 1

test-frontend:
	skedulord serve & ./node_modules/.bin/cypress run

build:
	docker build -t pythoncontainer .

test-gitlab:
	gitlab-runner exec docker test
