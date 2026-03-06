PYTHON ?= python

.PHONY: test check

test:
	$(PYTHON) -m unittest discover -s tests -p 'test_*.py'

check:
	$(PYTHON) -m compileall src
	$(MAKE) test
