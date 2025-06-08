"""
AWS Wrangler Testing Script
Demonstrates various AWS Wrangler operations for learning
"""

import awswrangler as wr
import pandas as pd
import yaml
import boto3
from datetime import datetime, timedelta
import os

def load_config():
    """Load configuration"""
    with open('config.yaml', 'r') as file:
        return yaml.safe_load(file)

def test_s3_operations(config):
    """Test basic S3 operations with AWS Wrangler"""
    print("=== Testing S3 Operations ===")
    
    session = boto3.Session(region_name=config['aws']['region'])
    bucket = config['aws']['s3_bucket']
    
    try:
        # Test 1: List S3 objects
        print("\n1. Listing S3 objects...")
        s3_path = f"s3://{bucket}/"
        objects = wr.s3.list_objects(s3_path, boto3_session=session)
        print(f"Found {len(objects)} objects in bucket")
        for obj in objects[:5]:  # Show first 5
            print(f"  - {obj}")
        
        # Test 2: Check if parquet file exists
        print("\n2. Checking for parquet files...")
        parquet_path = f"s3://{bucket}/{config['s3_paths']['news_parquet']}"
        if wr.s3.does_object_exist(parquet_path, boto3_session=session):
            print(f"✓ Parquet file exists: {parquet_path}")
            
            # Get file info
            file_info = wr.s3.describe_objects(parquet_path, boto3_session=session)
            size_mb = file_info[parquet_path]['ContentLength'] / (1024 * 1024)
            print(f"  File size: {size_mb:.2f} MB")
        else:
            print(f"✗ Parquet file not found: {parquet_path}")
        
        # Test 3: Read parquet metadata
        print("\n3. Reading parquet metadata...")
        try:
            metadata = wr.s3.read_parquet_metadata(parquet_path, boto3_session=session)
            print(f"✓ Parquet schema: {metadata[0].schema}")
        except Exception as e:
            print(f"✗ Could not read metadata: {e}")
        
    except Exception as e:
        print(f"✗ S3 operations failed: {e}")

def test_data_filtering(config):
    """Test data filtering operations"""
    print("\n=== Testing Data Filtering ===")
    
    session = boto3.Session(region_name=config['aws']['region'])
    bucket = config['aws']['s3_bucket']
    parquet_path = f"s3://{bucket}/{config['s3_paths']['news_parquet']}"
    
    try:
        # Read full dataset
        print("1. Reading full dataset...")
        df = wr.s3.read_parquet(parquet_path, boto3_session=session)
        print(f"✓ Loaded {len(df)} rows, {len(df.columns)} columns")
        
        # Test filtering by company
        print("\n2. Testing company filtering...")
        microsoft_data = df[df['company_name'] == 'Microsoft']
        print(f"✓ Microsoft articles: {len(microsoft_data)}")
        
        # Test date filtering
        print("\n3. Testing date filtering...")
        df['art2_date'] = pd.to_datetime(df['art2_date'])
        recent_cutoff = datetime.now() - timedelta(days=7)
        recent_data = df[df['art2_date'] >= recent_cutoff]
        print(f"✓ Recent articles (7 days): {len(recent_data)}")
        
        # Test sentiment filtering
        print("\n4. Testing sentiment filtering...")
        positive_sentiment = df[df['sentiment_score'] > 0.5]
        negative_sentiment = df[df['sentiment_score'] < -0.5]
        print(f"✓ Positive sentiment articles: {len(positive_sentiment)}")
        print(f"✓ Negative sentiment articles: {len(negative_sentiment)}")
        
        # Test column selection
        print("\n5. Testing column selection...")
        selected_cols = ['art2_title', 'company_name', 'sentiment_score', 'art2_date']
        df_subset = wr.s3.read_parquet(
            parquet_path, 
            columns=selected_cols,
            boto3_session=session
        )
        print(f"✓ Selected columns: {list(df_subset.columns)}")
        
    except Exception as e:
        print(f"✗ Data filtering failed: {e}")

def test_partitioned_reading(config):
    """Test reading partitioned data"""
    print("\n=== Testing Partitioned Data Reading ===")
    
    session = boto3.Session(region_name=config['aws']['region'])
    bucket = config['aws']['s3_bucket']
    partitioned_path = f"s3://{bucket}/{config['s3_paths']['news_data']}partitioned/"
    
    try:
        # Check if partitioned data exists
        if not wr.s3.does_object_exist(partitioned_path, boto3_session=session):
            print("✗ Partitioned data not found. Run export script first.")
            return
        
        # Read all partitioned data
        print("1. Reading all partitioned data...")
        df_all = wr.s3.read_parquet(partitioned_path, boto3_session=session)
        print(f"✓ Loaded {len(df_all)} rows from partitioned data")
        
        # Read specific partition
        print("\n2. Reading specific partition...")
        # Try to read Microsoft data only
        microsoft_path = f"{partitioned_path}company_name=Microsoft/"
        if wr.s3.does_object_exist(microsoft_path, boto3_session=session):
            df_microsoft = wr.s3.read_parquet(microsoft_path, boto3_session=session)
            print(f"✓ Microsoft partition: {len(df_microsoft)} rows")
        else:
            print("✗ Microsoft partition not found")
        
        # List all partitions
        print("\n3. Listing partitions...")
        partitions = wr.s3.list_objects(partitioned_path, boto3_session=session)
        partition_dirs = set()
        for obj in partitions:
            parts = obj.replace(partitioned_path, '').split('/')
            if len(parts) > 1:
                partition_dirs.add(parts[0])
        
        print(f"✓ Found {len(partition_dirs)} partition directories:")
        for partition in sorted(partition_dirs):
            print(f"  - {partition}")
        
    except Exception as e:
        print(f"✗ Partitioned reading failed: {e}")

def test_data_export(config):
    """Test data export operations"""
    print("\n=== Testing Data Export ===")
    
    session = boto3.Session(region_name=config['aws']['region'])
    bucket = config['aws']['s3_bucket']
    
    try:
        # Create sample data
        print("1. Creating sample data...")
        sample_data = pd.DataFrame({
            'id': range(1, 101),
            'name': [f'Test_{i}' for i in range(1, 101)],
            'value': pd.np.random.randn(100),
            'category': pd.np.random.choice(['A', 'B', 'C'], 100),
            'timestamp': pd.date_range('2024-01-01', periods=100, freq='H')
        })
        print(f"✓ Created sample data: {len(sample_data)} rows")
        
        # Test basic export
        print("\n2. Testing basic export...")
        test_path = f"s3://{bucket}/test_data/sample.parquet"
        wr.s3.to_parquet(
            df=sample_data,
            path=test_path,
            boto3_session=session
        )
        print(f"✓ Exported to: {test_path}")
        
        # Test partitioned export
        print("\n3. Testing partitioned export...")
        partitioned_test_path = f"s3://{bucket}/test_data/partitioned/"
        wr.s3.to_parquet(
            df=sample_data,
            path=partitioned_test_path,
            partition_cols=['category'],
            boto3_session=session
        )
        print(f"✓ Partitioned export to: {partitioned_test_path}")
        
        # Test CSV export
        print("\n4. Testing CSV export...")
        csv_path = f"s3://{bucket}/test_data/sample.csv"
        wr.s3.to_csv(
            df=sample_data,
            path=csv_path,
            index=False,
            boto3_session=session
        )
        print(f"✓ CSV export to: {csv_path}")
        
        # Verify exports by reading back
        print("\n5. Verifying exports...")
        df_parquet = wr.s3.read_parquet(test_path, boto3_session=session)
        df_csv = wr.s3.read_csv(csv_path, boto3_session=session)
        
        print(f"✓ Parquet verification: {len(df_parquet)} rows")
        print(f"✓ CSV verification: {len(df_csv)} rows")
        
    except Exception as e:
        print(f"✗ Data export failed: {e}")

def test_performance_comparison():
    """Compare AWS Wrangler vs direct boto3 performance"""
    print("\n=== Performance Comparison ===")
    
    # This is a conceptual test - actual implementation would need real data
    print("Performance comparison concepts:")
    print("1. AWS Wrangler benefits:")
    print("   - Automatic parallelization")
    print("   - Optimized data types")
    print("   - Built-in compression")
    print("   - Schema inference")
    
    print("\n2. Use cases for AWS Wrangler:")
    print("   - Large dataset processing")
    print("   - ETL pipelines")
    print("   - Data lake operations")
    print("   - Analytics workloads")
    
    print("\n3. When to use direct boto3:")
    print("   - Simple file operations")
    print("   - Non-tabular data")
    print("   - Custom S3 operations")
    print("   - Fine-grained control needed")

def main():
    """Run all AWS Wrangler tests"""
    print("=== AWS Wrangler Learning Tests ===")
    print("This script demonstrates various AWS Wrangler operations")
    
    # Load configuration
    config = load_config()
    
    # Run tests
    test_s3_operations(config)
    test_data_filtering(config)
    test_partitioned_reading(config)
    test_data_export(config)
    test_performance_comparison()
    
    print("\n=== Test Summary ===")
    print("✓ Completed AWS Wrangler learning tests")
    print("✓ Key patterns demonstrated:")
    print("  - S3 object operations")
    print("  - Parquet reading/writing")
    print("  - Data filtering")
    print("  - Partitioned data handling")
    print("  - Performance considerations")
    
    print("\nNext steps:")
    print("1. Experiment with different filter conditions")
    print("2. Try different compression formats")
    print("3. Test with larger datasets")
    print("4. Explore AWS Glue integration")

if __name__ == "__main__":
    main() 