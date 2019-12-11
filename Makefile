VIRTUAL_ENV ?= venv
PIP=$(VIRTUAL_ENV)/bin/pip
TOX=`which tox`
PYTHON=$(VIRTUAL_ENV)/bin/python
PYTHON_MAJOR_VERSION=3
PYTHON_MINOR_VERSION=7
SYSTEM_DEPENDENCIES= \
	libglfw3
PYTHON_VERSION=$(PYTHON_MAJOR_VERSION).$(PYTHON_MINOR_VERSION)
PYTHON_MAJOR_MINOR=$(PYTHON_MAJOR_VERSION)$(PYTHON_MINOR_VERSION)
PYTHON_WITH_VERSION=python$(PYTHON_VERSION)


all: virtualenv

system_dependencies:
	apt install --yes --no-install-recommends $(SYSTEM_DEPENDENCIES)

$(VIRTUAL_ENV):
	virtualenv -p $(PYTHON_WITH_VERSION) $(VIRTUAL_ENV)
	$(PIP) install -r requirements.txt

virtualenv: $(VIRTUAL_ENV)

run: virtualenv
	$(PYTHON) game.py
