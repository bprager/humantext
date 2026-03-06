PYTHON ?= python

.PHONY: test check version-check release-prep

version-check:
	PYTHONPATH=src $(PYTHON) scripts/check_version_sync.py


test:
	$(PYTHON) -m unittest discover -s tests -p 'test_*.py'

check:
	$(PYTHON) -m compileall src
	$(MAKE) version-check
	$(MAKE) test

release-prep:
	@test -n "$(VERSION)" || (echo "Usage: make release-prep VERSION=X.Y.Z" && exit 1)
	$(PYTHON) scripts/prepare_release.py $(VERSION)
