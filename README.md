# AWS Wrangler Learning Project - News Data Pipeline

This project simulates the key AWS Wrangler operations you'll work with in the news API system. It covers the main data flow patterns: data generation, S3 storage, and API serving.

## Project Overview

```
Data Generator → S3 Parquet Files → FastAPI → SQLite ↔ S3 Backup
     (AIGEN)         (Storage)        (API)      (Database)
```

## Learning Objectives

1. **AWS Wrangler S3 Operations**: Read/write parquet files efficiently
2. **Data Pipeline Patterns**: Batch processing and real-time serving
3. **Database Sync**: SQLite backup/restore with S3
4. **FastAPI Integration**: Serving data from pandas DataFrames
5. **Background Tasks**: Periodic data refresh and sync

## Prerequisites

- Python 3.8+
- AWS Account (free tier is sufficient)
- Basic knowledge of pandas and FastAPI

## Setup Instructions

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. AWS Configuration
```bash
# Configure AWS credentials
aws configure
# OR set environment variables:
export AWS_ACCESS_KEY_ID=your_key
export AWS_SECRET_ACCESS_KEY=your_secret
export AWS_DEFAULT_REGION=us-east-1
```

### 3. Create S3 Bucket
```bash
# Replace 'your-unique-bucket-name' with your bucket name
aws s3 mb s3://your-learning-bucket-name
```

### 4. Update Configuration
Edit `config.yaml` with your S3 bucket name.

## Project Structure

```
├── data_generator/          # Simulates AIGEN data generation
│   ├── generate_news.py     # Creates sample news data
│   └── export_to_s3.py      # Exports data using AWS Wrangler
├── api/                     # Simulates FastAPI backend
│   ├── app.py              # FastAPI application
│   ├── database.py         # SQLite operations
│   └── s3_sync.py          # S3 sync operations
├── scripts/                # Utility scripts
│   ├── setup_data.py       # Initial data setup
│   └── test_pipeline.py    # Test the complete pipeline
├── config.yaml             # Configuration file
├── requirements.txt        # Python dependencies
└── README.md              # This file
```

## Learning Exercises

### Exercise 1: Data Generation and Export
Run the data generator to create sample news data and export to S3:
```bash
python data_generator/generate_news.py
python data_generator/export_to_s3.py
```

### Exercise 2: FastAPI Data Loading
Start the FastAPI server that loads data from S3:
```bash
python api/app.py
```

### Exercise 3: Database Sync Operations
Test SQLite backup and restore:
```bash
python api/s3_sync.py --backup
python api/s3_sync.py --restore
```

### Exercise 4: Complete Pipeline Test
Run the full pipeline simulation:
```bash
python scripts/test_pipeline.py
```

## Key AWS Wrangler Patterns You'll Learn

1. **Efficient Parquet Operations**
2. **Partitioned Data Storage**
3. **Batch vs Streaming Operations**
4. **Memory-Optimized Data Loading**
5. **Error Handling and Retries**

## API Endpoints

- `GET /health` - Health check
- `GET /news` - Get news data (from loaded DataFrame)
- `GET /news/search?q=keyword` - Search news
- `POST /refresh` - Refresh data from S3
- `GET /stats` - Data statistics

## Next Steps

After completing this project, you'll understand:
- How AWS Wrangler optimizes pandas + S3 operations
- Data pipeline patterns used in production
- Background task management in FastAPI
- Database sync strategies

This knowledge directly applies to the news API system you'll be working on. 