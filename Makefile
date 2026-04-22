.PHONY: setup run test clean

PYTHON = python3
PIP = pip3

setup:
	$(PIP) install -r requirements.txt

run:
	$(PYTHON) -m src.simulation.runner --config config/simulation_params.yaml

test:
	python tests/test_full_project.py

test-quick:
	python tests/test_full_project.py 2>&1 | grep -E "(PHASE|✅|❌|RESULTS)"

test-api:
	pytest tests/test_api.py -v

test-coverage:
	python -m pytest tests/ --cov=src --cov-report=html

validate:
	@echo "Running full validation suite..."
	make test
	make simulate-10
	@echo "✅ Validation complete"

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	rm -rf .pytest_cache
	rm -rf results/*.csv

dashboard:
	uvicorn src.api.main:app --reload

competitive:
	$(PYTHON) -m scripts.compare_campaigns

predict:
	$(PYTHON) -m src.analytics.reports --predict

pipeline:
	$(PYTHON) -m scripts.run_simulation && $(PYTHON) -m scripts.generate_report
max-simulate:
	export PYTHONPATH=$(shell pwd)/src && python3 -c "from core.max_engine import MaxSimulation; s = MaxSimulation('config/agents_10.yaml'); s.initialize(); s.run(days=7); print('Advanced simulation complete')"

max-test:
	export PYTHONPATH=$(shell pwd)/src && python3 -c "from core.max_engine import MaxSimulation; s = MaxSimulation('config/agents_10.yaml'); s.initialize(); s.run(days=2); print('CLV:', s.predict_clv('Budget_Brian')); print('Intervention:', s.recommend_churn_intervention('Budget_Brian')); print('Price War:', s.run_price_war_simulation(20)); print('Market Entry:', s.analyze_market_entry()); print('Trends:', s.detect_market_trends())"
