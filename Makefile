PYTHON ?= python

install:
	$(PYTHON) -m pip install -e ".[dev]"

test:
	$(PYTHON) -m pytest

compile:
	$(PYTHON) -m compileall -q src drivers sdk tests

check:
	$(PYTHON) tools/dev.py check

site:
	$(PYTHON) tools/site/build.py

release-check:
	$(PYTHON) tools/dev.py release-check
