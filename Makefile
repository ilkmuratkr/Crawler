.PHONY: help install test clean run examples

help:
	@echo "Common Crawl Next.js Detector"
	@echo ""
	@echo "Available commands:"
	@echo "  make install        - Install dependencies"
	@echo "  make test          - Run component tests"
	@echo "  make clean         - Clean output and logs"
	@echo "  make run           - Run basic search"
	@echo "  make bulk          - Run bulk WARC search"
	@echo "  make process        - Process WARC files (ADVANCED - with retry)"
	@echo "  make process-test   - Process first 10 WARCs (test)"
	@echo "  make process-small  - Process first 100 WARCs"
	@echo "  make process-large  - Process 1000 WARCs"
	@echo "  make resume         - Resume from last failures"
	@echo "  make examples      - Run all examples"

install:
	pip install -r requirements.txt
	mkdir -p data/output logs

test:
	python examples/test_components.py

clean:
	rm -rf data/output/*.json data/output/*.csv
	rm -rf logs/*.log
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

run:
	python main.py --pattern "*.com/" --limit 100 --workers 5

bulk:
	python examples/bulk_warc_search.py --index CC-MAIN-2025-47 --max-files 50 --workers 5

examples:
	@echo "Running simple search..."
	python examples/simple_search.py
	@echo ""
	@echo "Running specific domains check..."
	python examples/specific_domains.py

quick-test:
	python main.py --pattern "vercel.com" --limit 5 --log-level DEBUG

format:
	black src/ examples/ main.py

lint:
	flake8 src/ examples/ main.py --max-line-length=100

# WARC Processing Commands (ADVANCED)
process:
	python process_warcs.py --limit 1000 --workers 10

process-test:
	python process_warcs.py --limit 10 --workers 3 --retry-delay 30

process-small:
	python process_warcs.py --limit 100 --workers 5

process-large:
	python process_warcs.py --limit 1000 --workers 10

process-full:
	@echo "⚠️  WARNING: This will process ALL 100,000 WARCs!"
	@echo "This will take DAYS to complete."
	python process_warcs.py --workers 10

resume:
	@echo "Finding latest failure file..."
	@latest=$$(ls -t data/failures/failed_warcs_*.json 2>/dev/null | head -1); \
	if [ -z "$$latest" ]; then \
		echo "No failure files found."; \
	else \
		echo "Resuming from: $$latest"; \
		python process_warcs.py --resume-from "$$latest" --workers 10; \
	fi
