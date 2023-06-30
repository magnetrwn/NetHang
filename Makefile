.PHONY: clean
clean:
	rm -rf dist *.egg-info

.PHONY: requirements
requirements:
	pip3 install -r requirements.txt

.PHONY: test
test: requirements
	pytest

.PHONY: build
build: clean requirements
	python3 -m build

.PHONY: install
install: build
	pip3 install --force-reinstall dist/*.whl
