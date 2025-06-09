"""
S3 Bucket Setup Script
Creates the S3 bucket and uploads mock data for the AWS Wrangler learning project
"""

import boto3
import pandas as pd
import awswrangler as wr
import yaml
import os
from datetime import datetime, timedelta
import random
from faker import Faker
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

fake = Faker()

def load_config():
    """Load configuration from config.yaml"""
    with open('config.yaml', 'r') as file:
        return yaml.safe_load(file)

def setup_aws_session(config):
    """Setup AWS session with credentials"""
    try:
        aws_access_key_id = os.getenv('AWS_ACCESS_KEY_ID')
        aws_secret_access_key = os.getenv('AWS_SECRET_ACCESS_KEY')
        aws_region = os.getenv('AWS_DEFAULT_REGION', config['aws']['region'])
        
        if aws_access_key_id and aws_secret_access_key:
            session = boto3.Session(
                aws_access_key_id=aws_access_key_id,
                aws_secret_access_key=aws_secret_access_key,
                region_name=aws_region
            )
            print(f"✓ AWS session created for region: {aws_region}")
            return session
        else:
            print("✗ AWS credentials not found in environment variables")
            return None
    except Exception as e:
        print(f"✗ Failed to create AWS session: {e}")
        return None

def create_s3_bucket(session, bucket_name, region):
    """Create S3 bucket if it doesn't exist"""
    try:
        s3_client = session.client('s3')
        
        # Check if bucket already exists
        try:
            s3_client.head_bucket(Bucket=bucket_name)
            print(f"✓ S3 bucket '{bucket_name}' already exists")
            return True
        except Exception as e:
            # Bucket doesn't exist, we'll create it
            print(f"Bucket doesn't exist, creating: {bucket_name}")
        
        # Create bucket
        try:
            if region == 'us-east-1':
                # us-east-1 doesn't need LocationConstraint
                s3_client.create_bucket(Bucket=bucket_name)
            else:
                s3_client.create_bucket(
                    Bucket=bucket_name,
                    CreateBucketConfiguration={'LocationConstraint': region}
                )
            
            print(f"✓ Created S3 bucket: {bucket_name}")
            return True
            
        except Exception as create_error:
            print(f"✗ Failed to create bucket: {create_error}")
            return False
        
    except Exception as e:
        print(f"✗ Failed to create S3 bucket: {e}")
        return False

def generate_mock_news_data(num_articles=500):
    """Generate mock news data similar to the actual system"""
    print(f"Generating {num_articles} mock news articles...")
    
    companies = ["Microsoft", "Google", "Apple", "Amazon", "Tesla", "Meta", "Netflix"]
    categories = ["Technology", "Business", "Finance", "AI", "Cloud", "Security"]
    
    articles = []
    
    for i in range(num_articles):
        company = random.choice(companies)
        category = random.choice(categories)
        
        article = {
            'id': i + 1,
            'url': fake.url(),
            'url_final': fake.url(),
            'source': random.choice(['Google News', 'Bing News', 'PR Newswire', 'Yahoo Finance']),
            'art_title': f"{company} {fake.catch_phrase()}",
            'art2_title': f"{company} {fake.catch_phrase()}",
            'art2_text': fake.text(max_nb_chars=1000),
            'art2_content': fake.text(max_nb_chars=2000),
            'art2_url': fake.url(),
            'art2_date': fake.date_time_between(start_date='-30d', end_date='now'),
            'company_name': company,
            'company_id': f"com_{company.lower().replace(' ', '_')}",
            'category': category,
            'category_score': random.uniform(0.7, 0.99),
            'sentiment_score': random.uniform(-1, 1),
            'sentiment_label': random.choice(['positive', 'negative', 'neutral']),
            'summary': fake.sentence(nb_words=20),
            'processed_date': datetime.now(),
            'data_source': 'mock_generated',
            'is_valid': True,
            'priority_score': random.uniform(0, 1)
        }
        
        articles.append(article)
    
    df = pd.DataFrame(articles)
    print(f"✓ Generated {len(df)} mock articles")
    return df

def upload_mock_data_to_s3(session, df, config):
    """Upload mock data to S3 in the expected format"""
    bucket = config['aws']['s3_bucket']
    
    try:
        # Upload main parquet file
        main_s3_path = f"s3://{bucket}/{config['s3_paths']['news_parquet']}"
        print(f"Uploading main data to: {main_s3_path}")
        
        wr.s3.to_parquet(
            df=df,
            path=main_s3_path,
            boto3_session=session
        )
        print(f"✓ Uploaded main parquet file")
        
        # Upload partitioned data
        partitioned_path = f"s3://{bucket}/{config['s3_paths']['news_data']}partitioned/"
        print(f"Uploading partitioned data to: {partitioned_path}")
        
        # Add partition columns
        df_partitioned = df.copy()
        df_partitioned['year'] = df_partitioned['art2_date'].dt.year
        df_partitioned['month'] = df_partitioned['art2_date'].dt.month
        
        wr.s3.to_parquet(
            df=df_partitioned,
            path=partitioned_path,
            partition_cols=['year', 'month', 'company_name'],
            compression='snappy',
            dataset=True,
            boto3_session=session
        )
        print(f"✓ Uploaded partitioned data")
        
        # Upload daily data
        daily_path = f"s3://{bucket}/{config['s3_paths']['news_data']}daily/"
        print(f"Uploading daily data to: {daily_path}")
        
        df_daily = df.copy()
        df_daily['date'] = df_daily['art2_date'].dt.date.astype(str)
        
        wr.s3.to_parquet(
            df=df_daily,
            path=daily_path,
            partition_cols=['date'],
            dataset=True,
            boto3_session=session
        )
        
        print(f"✓ Uploaded daily partitioned data")
        
        # Create metadata
        metadata = {
            'export_timestamp': datetime.now().isoformat(),
            'total_articles': len(df),
            'companies': df['company_name'].unique().tolist(),
            'categories': df['category'].unique().tolist(),
            'data_version': '1.0',
            'export_type': 'mock_data'
        }
        
        metadata_df = pd.DataFrame([metadata])
        metadata_path = f"s3://{bucket}/{config['s3_paths']['news_data']}metadata/export_info.parquet"
        
        wr.s3.to_parquet(
            df=metadata_df,
            path=metadata_path,
            boto3_session=session
        )
        print(f"✓ Uploaded metadata")
        
        return True
        
    except Exception as e:
        print(f"✗ Failed to upload data to S3: {e}")
        return False

def create_sample_users_data(session, config):
    """Create sample users data for database sync testing"""
    try:
        users_data = {
            'id': [1, 2, 3, 4, 5],
            'username': ['demo_user', 'test_user', 'admin', 'analyst', 'viewer'],
            'email': ['demo@example.com', 'test@example.com', 'admin@example.com', 
                     'analyst@example.com', 'viewer@example.com'],
            'created_at': [datetime.now() - timedelta(days=i) for i in range(5)],
            'last_login': [datetime.now() - timedelta(hours=i) for i in range(5)]
        }
        
        users_df = pd.DataFrame(users_data)
        bucket = config['aws']['s3_bucket']
        users_path = f"s3://{bucket}/{config['s3_paths']['database_backup']}"
        
        wr.s3.to_parquet(
            df=users_df,
            path=users_path,
            boto3_session=session
        )
        print(f"✓ Uploaded sample users data")
        return True
        
    except Exception as e:
        print(f"✗ Failed to upload users data: {e}")
        return False

def main():
    """Main function to set up S3 bucket and mock data"""
    print("=== S3 Bucket Setup for AWS Wrangler Learning Project ===")
    
    # Load configuration
    config = load_config()
    bucket_name = config['aws']['s3_bucket']
    region = config['aws']['region']
    
    print(f"Target bucket: {bucket_name}")
    print(f"Region: {region}")
    
    # Setup AWS session
    session = setup_aws_session(config)
    if not session:
        print("Please check your AWS credentials in .env file")
        return False
    
    # Create S3 bucket
    if not create_s3_bucket(session, bucket_name, region):
        return False
    
    # Generate mock data
    df = generate_mock_news_data(num_articles=500)
    
    # Upload data to S3
    if not upload_mock_data_to_s3(session, df, config):
        return False
    
    # Create sample users data
    create_sample_users_data(session, config)
    
    print("\n=== Setup Complete ===")
    print(f"✓ S3 bucket '{bucket_name}' is ready")
    print(f"✓ Mock data uploaded successfully")
    print(f"✓ Your FastAPI app should now work without errors")
    print("\nNext steps:")
    print("1. Run: make start")
    print("2. Visit: http://localhost:8000/health")
    print("3. Try: http://localhost:8000/news")
    
    return True

if __name__ == "__main__":
    success = main()
    if not success:
        print("\n✗ Setup failed. Please check the errors above.")
        exit(1)
    else:
        print("\n🎉 S3 setup completed successfully!")
        exit(0) 