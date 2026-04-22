.PHONY: clean test run-ab help

# Variables
AD1 = "Save 50% on your first purchase today!"
AD2 = "Experience luxury like never before."
AGENTS = 500

help:
	@echo "Marketing Simulation Engine - Commands"
	@echo "--------------------------------------"
	@echo "test        : Run all unit tests"
	@echo "run-ab      : Run a default A/B test simulation"
	@echo "clean       : Remove caches and junk files"
	@echo "cli         : Show how to use the CLI"

test:
	export PYTHONPATH=. && python -m pytest tests/

run-ab:
	export PYTHONPATH=. && python cli.py --ad1 "$(AD1)" --ad2 "$(AD2)" --agents $(AGENTS)

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	rm -f *.log *.json c.txt report.json .env

cli:
	python cli.py --help
