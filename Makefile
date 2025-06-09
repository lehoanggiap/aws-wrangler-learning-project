.PHONY: start dev install test clean generate export

# Start the FastAPI server
start:
	python3 api/app.py

# Start with auto-reload (development mode)
dev:
	uvicorn api.app:app --reload --host 0.0.0.0 --port 8000

# Install dependencies
install:
	uv pip install -r requirements.txt

# Generate sample data
generate:
	python3 data_generator/generate_news.py

# Export data to S3
export:
	python3 data_generator/export_to_s3.py

# Test AWS Wrangler operations
test:
	python3 scripts/test_wrangler.py

# Setup project
setup:
	python3 scripts/setup.py

# Clean generated data
clean:
	rm -rf data/

# Run full pipeline
pipeline: generate export start 