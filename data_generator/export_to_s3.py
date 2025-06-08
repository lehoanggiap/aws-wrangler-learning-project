"""
S3 Export Script - Demonstrates AWS Wrangler usage
Simulates the AIGEN data export process to S3
"""

import awswrangler as wr
import pandas as pd
import yaml
import boto3
from datetime import datetime
import os

def load_config():
    """Load configuration from config.yaml"""
    with open('config.yaml', 'r') as file:
        return yaml.safe_load(file)

def setup_aws_session(config):
    """Setup AWS session and validate S3 access"""
    try:
        # Create boto3 session
        session = boto3.Session(region_name=config['aws']['region'])
        
        # Test S3 access
        s3_client = session.client('s3')
        bucket_name = config['aws']['s3_bucket']
        
        # Check if bucket exists
        try:
            s3_client.head_bucket(Bucket=bucket_name)
            print(f"✓ S3 bucket '{bucket_name}' is accessible")
        except Exception as e:
            print(f"✗ Cannot access S3 bucket '{bucket_name}': {e}")
            print("Please check your AWS credentials and bucket name in config.yaml")
            return None
            
        return session
        
    except Exception as e:
        print(f"✗ AWS setup failed: {e}")
        print("Please run 'aws configure' or set AWS environment variables")
        return None

def export_news_data_basic(df, config, session):
    """Basic AWS Wrangler export - single parquet file"""
    print("\n=== Basic Export (Single Parquet File) ===")
    
    bucket = config['aws']['s3_bucket']
    s3_path = f"s3://{bucket}/{config['s3_paths']['news_parquet']}"
    
    print(f"Exporting to: {s3_path}")
    
    try:
        # Basic export using AWS Wrangler
        wr.s3.to_parquet(
            df=df,
            path=s3_path,
            boto3_session=session
        )
        print("✓ Basic export completed successfully")
        
        # Verify the export
        file_info = wr.s3.describe_objects(s3_path, boto3_session=session)
        print(f"✓ File size: {file_info[s3_path]['ContentLength']} bytes")
        
    except Exception as e:
        print(f"✗ Basic export failed: {e}")

def export_news_data_partitioned(df, config, session):
    """Advanced AWS Wrangler export - partitioned data"""
    print("\n=== Advanced Export (Partitioned Data) ===")
    
    bucket = config['aws']['s3_bucket']
    s3_path = f"s3://{bucket}/{config['s3_paths']['news_data']}partitioned/"
    
    print(f"Exporting partitioned data to: {s3_path}")
    
    try:
        # Add partition columns
        df_partitioned = df.copy()
        df_partitioned['year'] = df_partitioned['art2_date'].dt.year
        df_partitioned['month'] = df_partitioned['art2_date'].dt.month
        
        # Partitioned export using AWS Wrangler
        wr.s3.to_parquet(
            df=df_partitioned,
            path=s3_path,
            partition_cols=['year', 'month', 'company_name'],
            compression='snappy',
            boto3_session=session
        )
        print("✓ Partitioned export completed successfully")
        
        # List partitions
        partitions = wr.s3.list_objects(s3_path, boto3_session=session)
        print(f"✓ Created {len(partitions)} partition files")
        
    except Exception as e:
        print(f"✗ Partitioned export failed: {e}")

def export_news_data_incremental(df, config, session):
    """Incremental export - simulates daily data updates"""
    print("\n=== Incremental Export (Daily Updates) ===")
    
    bucket = config['aws']['s3_bucket']
    base_path = f"s3://{bucket}/{config['s3_paths']['news_data']}daily/"
    
    # Split data by date for incremental export
    df['date'] = df['art2_date'].dt.date
    unique_dates = df['date'].unique()
    
    print(f"Exporting {len(unique_dates)} daily files...")
    
    try:
        for date in unique_dates:
            daily_df = df[df['date'] == date].copy()
            daily_path = f"{base_path}date={date}/data.parquet"
            
            # Export daily data
            wr.s3.to_parquet(
                df=daily_df,
                path=daily_path,
                boto3_session=session
            )
            print(f"✓ Exported {len(daily_df)} articles for {date}")
            
        print("✓ Incremental export completed successfully")
        
    except Exception as e:
        print(f"✗ Incremental export failed: {e}")

def test_data_reading(config, session):
    """Test reading data back from S3 using AWS Wrangler"""
    print("\n=== Testing Data Reading ===")
    
    bucket = config['aws']['s3_bucket']
    s3_path = f"s3://{bucket}/{config['s3_paths']['news_parquet']}"
    
    try:
        # Read data back using AWS Wrangler
        print(f"Reading data from: {s3_path}")
        df_read = wr.s3.read_parquet(s3_path, boto3_session=session)
        
        print(f"✓ Successfully read {len(df_read)} rows")
        print(f"✓ Columns: {list(df_read.columns)}")
        print(f"✓ Memory usage: {df_read.memory_usage(deep=True).sum() / 1024**2:.2f} MB")
        
        # Test filtering (simulates API queries)
        microsoft_news = df_read[df_read['company_name'] == 'Microsoft']
        print(f"✓ Microsoft articles: {len(microsoft_news)}")
        
        recent_news = df_read[df_read['art2_date'] >= pd.Timestamp.now() - pd.Timedelta(days=7)]
        print(f"✓ Recent articles (7 days): {len(recent_news)}")
        
    except Exception as e:
        print(f"✗ Data reading failed: {e}")

def export_metadata(config, session):
    """Export metadata and statistics"""
    print("\n=== Exporting Metadata ===")
    
    bucket = config['aws']['s3_bucket']
    
    # Create metadata
    metadata = {
        'export_timestamp': datetime.now().isoformat(),
        'total_articles': 1000,  # From config
        'companies': config['data_generation']['companies'],
        'categories': config['data_generation']['categories'],
        'data_version': '1.0',
        'export_type': 'learning_project'
    }
    
    metadata_df = pd.DataFrame([metadata])
    metadata_path = f"s3://{bucket}/{config['s3_paths']['news_data']}metadata/export_info.parquet"
    
    try:
        wr.s3.to_parquet(
            df=metadata_df,
            path=metadata_path,
            boto3_session=session
        )
        print(f"✓ Metadata exported to: {metadata_path}")
        
    except Exception as e:
        print(f"✗ Metadata export failed: {e}")

def main():
    """Main function to demonstrate AWS Wrangler S3 operations"""
    print("=== AWS Wrangler S3 Export Demo ===")
    print("Simulating AIGEN data export process...")
    
    # Load configuration
    config = load_config()
    
    # Setup AWS session
    session = setup_aws_session(config)
    if not session:
        return
    
    # Load local data
    local_path = 'data/df_all_news.parquet'
    if not os.path.exists(local_path):
        print(f"✗ Local data file not found: {local_path}")
        print("Please run 'python data_generator/generate_news.py' first")
        return
    
    print(f"Loading data from: {local_path}")
    df = pd.read_parquet(local_path)
    print(f"✓ Loaded {len(df)} articles")
    
    # Demonstrate different export patterns
    export_news_data_basic(df, config, session)
    export_news_data_partitioned(df, config, session)
    export_news_data_incremental(df, config, session)
    export_metadata(config, session)
    
    # Test reading data back
    test_data_reading(config, session)
    
    print("\n=== Export Summary ===")
    print("✓ Demonstrated AWS Wrangler patterns:")
    print("  - Basic parquet export")
    print("  - Partitioned data export")
    print("  - Incremental daily exports")
    print("  - Metadata export")
    print("  - Data reading and filtering")
    
    print("\nNext step: Run 'python api/app.py' to start the FastAPI server")

if __name__ == "__main__":
    main() 