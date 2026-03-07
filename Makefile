PYTHON ?= python

.PHONY: lint test coverage check version-check release-prep

lint:
	$(PYTHON) -m compileall src tests scripts


version-check:
	PYTHONPATH=src $(PYTHON) scripts/check_version_sync.py


test:
	$(PYTHON) -m unittest discover -s tests -p 'test_*.py'

coverage:
	$(PYTHON) -m coverage run -m unittest discover -s tests -p 'test_*.py'
	$(PYTHON) -m coverage xml
	$(PYTHON) -m coverage report

check:
	$(MAKE) lint
	$(MAKE) version-check
	$(MAKE) test

release-prep:
	@test -n "$(VERSION)" || (echo "Usage: make release-prep VERSION=X.Y.Z" && exit 1)
	$(PYTHON) scripts/prepare_release.py $(VERSION)
