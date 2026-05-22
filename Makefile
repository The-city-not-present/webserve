.PHONY: build init test run



PYTEST=python -m pytest
define BROWSER_PYSCRIPT
import os, webbrowser, sys
try:
	from urllib import pathname2url
except:
	from urllib.request import pathname2url

webbrowser.open("file://" + pathname2url(os.path.abspath(sys.argv[1])))
endef
export BROWSER_PYSCRIPT
BROWSER := python -c "$$BROWSER_PYSCRIPT"



build:
	./build-scripts/build.sh



init:
	./build-scripts/init.sh



test:
	$(PYTEST)



test-html:
	mkdir -p test-results
	$(PYTEST) --html=test-results/report.html --self-contained-html
	$(BROWSER) test-results/report.html



test-cov:
	$(PYTEST) --cov



run:
	./build-scripts/run.sh
