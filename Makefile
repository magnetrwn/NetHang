.PHONY: clean
clean:
	rm -rf dist *.egg-info

.PHONY: test
test: clean
	pytest

.PHONY: build
build: clean test
	python3 -m build

.PHONY: install
install: clean test build
	pip3 install --force-reinstall dist/*.whl
