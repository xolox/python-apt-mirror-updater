# Makefile for the 'apt-mirror-updater' package.
#
# Author: Peter Odding <peter@peterodding.com>
# Last Change: April 15, 2020
# URL: https://apt-mirror-updater.readthedocs.io

PACKAGE_NAME = apt-mirror-updater
WORKON_HOME ?= $(HOME)/.virtualenvs
VIRTUAL_ENV ?= $(WORKON_HOME)/$(PACKAGE_NAME)
PYTHON ?= python3
PATH := $(VIRTUAL_ENV)/bin:$(PATH)
MAKE := $(MAKE) --no-print-directory
SHELL = bash

default:
	@echo "Makefile for $(PACKAGE_NAME)"
	@echo
	@echo 'Usage:'
	@echo
	@echo '    make install    install the package in a virtual environment'
	@echo '    make reset      recreate the virtual environment'
	@echo '    make check      check coding style (PEP-8, PEP-257)'
	@echo '    make test       run the test suite, report coverage'
	@echo '    make tox        run the tests on all Python versions'
	@echo '    make releases   update apt_mirror_updater.releases module'
	@echo '    make readme     update usage in readme'
	@echo '    make docs       update documentation using Sphinx'
	@echo '    make publish    publish changes to GitHub/PyPI'
	@echo '    make clean      cleanup all temporary files'
	@echo

install:
	@test -d "$(VIRTUAL_ENV)" || mkdir -p "$(VIRTUAL_ENV)"
	@test -x "$(VIRTUAL_ENV)/bin/python" || virtualenv --python=$(PYTHON) --quiet "$(VIRTUAL_ENV)"
	@pip install --quiet --requirement=requirements.txt
	@pip uninstall --yes $(PACKAGE_NAME) &>/dev/null || true
	@pip install --quiet --no-deps --ignore-installed .

reset:
	$(MAKE) clean
	rm -Rf "$(VIRTUAL_ENV)"
	$(MAKE) install

check: install
	@pip install --upgrade --quiet --requirement=requirements-checks.txt
	@flake8

test: install
	@pip install --quiet --requirement=requirements-tests.txt
	@py.test --cov
	@coverage html

tox: install
	@pip install --quiet tox && tox

# The following makefile target isn't documented on purpose, I don't want
# people to execute this without them knowing very well what they're doing.

full-coverage: install
	@pip install --quiet --requirement=requirements-tests.txt
	@scripts/collect-full-coverage.sh
	@coverage html

cog: install
	@echo Installing cog ...
	@pip install --quiet cogapp

releases: cog
	@cog.py -r apt_mirror_updater/releases.py

readme: cog
	@cog.py -r README.rst

docs: releases readme
	@pip install --quiet sphinx
	@cd docs && sphinx-build -nb html -d build/doctrees . build/html

publish: install
	git push origin && git push --tags origin
	$(MAKE) clean
	pip install --quiet twine wheel
	python setup.py sdist bdist_wheel
	twine upload dist/*
	$(MAKE) clean

clean:
	@rm -Rf *.egg .cache .coverage .tox build dist docs/build htmlcov
	@find -depth -type d -name __pycache__ -exec rm -Rf {} \;
	@find -type f -name '*.pyc' -delete

.PHONY: default install reset check test tox readme docs publish clean
