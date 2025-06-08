"""
Setup Script for AWS Wrangler Learning Project
Helps initialize the project and check prerequisites
"""

import os
import sys
import subprocess
import yaml
import boto3
from pathlib import Path

def check_python_version():
    """Check if Python version is compatible"""
    print("=== Checking Python Version ===")
    version = sys.version_info
    if version.major == 3 and version.minor >= 8:
        print(f"✓ Python {version.major}.{version.minor}.{version.micro} is compatible")
        return True
    else:
        print(f"✗ Python {version.major}.{version.minor}.{version.micro} is not compatible")
        print("Please use Python 3.8 or higher")
        return False

def check_aws_credentials():
    """Check if AWS credentials are configured"""
    print("\n=== Checking AWS Credentials ===")
    try:
        session = boto3.Session()
        credentials = session.get_credentials()
        
        if credentials is None:
            print("✗ AWS credentials not found")
            print("Please run 'aws configure' or set environment variables:")
            print("  - AWS_ACCESS_KEY_ID")
            print("  - AWS_SECRET_ACCESS_KEY")
            print("  - AWS_DEFAULT_REGION")
            return False
        else:
            print("✓ AWS credentials found")
            
            # Test credentials by listing S3 buckets
            try:
                s3_client = session.client('s3')
                s3_client.list_buckets()
                print("✓ AWS credentials are valid")
                return True
            except Exception as e:
                print(f"✗ AWS credentials test failed: {e}")
                return False
                
    except Exception as e:
        print(f"✗ Error checking AWS credentials: {e}")
        return False

def check_s3_bucket(config):
    """Check if S3 bucket exists and is accessible"""
    print("\n=== Checking S3 Bucket ===")
    try:
        session = boto3.Session(region_name=config['aws']['region'])
        s3_client = session.client('s3')
        bucket_name = config['aws']['s3_bucket']
        
        # Check if bucket exists
        try:
            s3_client.head_bucket(Bucket=bucket_name)
            print(f"✓ S3 bucket '{bucket_name}' is accessible")
            return True
        except s3_client.exceptions.NoSuchBucket:
            print(f"✗ S3 bucket '{bucket_name}' does not exist")
            
            # Offer to create bucket
            create = input("Would you like to create this bucket? (y/n): ").lower()
            if create == 'y':
                try:
                    if config['aws']['region'] == 'us-east-1':
                        s3_client.create_bucket(Bucket=bucket_name)
                    else:
                        s3_client.create_bucket(
                            Bucket=bucket_name,
                            CreateBucketConfiguration={'LocationConstraint': config['aws']['region']}
                        )
                    print(f"✓ Created S3 bucket '{bucket_name}'")
                    return True
                except Exception as e:
                    print(f"✗ Failed to create bucket: {e}")
                    return False
            else:
                print("Please update the bucket name in config.yaml")
                return False
        except Exception as e:
            print(f"✗ Error accessing bucket: {e}")
            return False
            
    except Exception as e:
        print(f"✗ Error checking S3 bucket: {e}")
        return False

def install_dependencies():
    """Install required Python packages"""
    print("\n=== Installing Dependencies ===")
    try:
        print("Installing packages from requirements.txt...")
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", "-r", "requirements.txt"
        ])
        print("✓ Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ Failed to install dependencies: {e}")
        return False

def create_directories():
    """Create necessary directories"""
    print("\n=== Creating Directories ===")
    directories = [
        'data',
        'data_generator',
        'api',
        'scripts',
        'database'
    ]
    
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        print(f"✓ Created directory: {directory}")
    
    return True

def validate_config():
    """Validate configuration file"""
    print("\n=== Validating Configuration ===")
    try:
        with open('config.yaml', 'r') as file:
            config = yaml.safe_load(file)
        
        # Check required sections
        required_sections = ['aws', 's3_paths', 'database', 'data_generation', 'api']
        for section in required_sections:
            if section not in config:
                print(f"✗ Missing section in config.yaml: {section}")
                return None
        
        # Check AWS configuration
        if not config['aws']['s3_bucket']:
            print("✗ S3 bucket name not set in config.yaml")
            print("Please update the 's3_bucket' field with your bucket name")
            return None
        
        print("✓ Configuration file is valid")
        return config
        
    except FileNotFoundError:
        print("✗ config.yaml not found")
        return None
    except yaml.YAMLError as e:
        print(f"✗ Error parsing config.yaml: {e}")
        return None

def run_initial_data_generation():
    """Run initial data generation"""
    print("\n=== Generating Initial Data ===")
    try:
        print("Running data generation script...")
        subprocess.check_call([sys.executable, "data_generator/generate_news.py"])
        print("✓ Initial data generated successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ Data generation failed: {e}")
        return False
    except FileNotFoundError:
        print("✗ Data generation script not found")
        return False

def print_next_steps():
    """Print next steps for the user"""
    print("\n=== Next Steps ===")
    print("Your AWS Wrangler learning project is ready! Here's what to do next:")
    print()
    print("1. Generate sample data:")
    print("   python data_generator/generate_news.py")
    print()
    print("2. Export data to S3:")
    print("   python data_generator/export_to_s3.py")
    print()
    print("3. Start the FastAPI server:")
    print("   python api/app.py")
    print()
    print("4. Test AWS Wrangler operations:")
    print("   python scripts/test_wrangler.py")
    print()
    print("5. Access the API documentation:")
    print("   http://localhost:8000/docs")
    print()
    print("6. Try the API endpoints:")
    print("   - http://localhost:8000/health")
    print("   - http://localhost:8000/news")
    print("   - http://localhost:8000/companies")
    print("   - http://localhost:8000/stats")

def main():
    """Main setup function"""
    print("=== AWS Wrangler Learning Project Setup ===")
    print("This script will help you set up the learning environment")
    print()
    
    # Check prerequisites
    if not check_python_version():
        return False
    
    # Create directories
    create_directories()
    
    # Validate configuration
    config = validate_config()
    if not config:
        return False
    
    # Install dependencies
    install_choice = input("Install Python dependencies? (y/n): ").lower()
    if install_choice == 'y':
        if not install_dependencies():
            return False
    
    # Check AWS setup
    aws_choice = input("Check AWS credentials and S3 bucket? (y/n): ").lower()
    if aws_choice == 'y':
        if not check_aws_credentials():
            print("Please configure AWS credentials before proceeding")
            return False
        
        if not check_s3_bucket(config):
            print("Please fix S3 bucket configuration before proceeding")
            return False
    
    # Generate initial data
    data_choice = input("Generate initial sample data? (y/n): ").lower()
    if data_choice == 'y':
        run_initial_data_generation()
    
    print("\n=== Setup Complete ===")
    print("✓ AWS Wrangler learning project setup completed successfully!")
    
    print_next_steps()
    
    return True

if __name__ == "__main__":
    success = main()
    if not success:
        print("\n✗ Setup encountered issues. Please resolve them before proceeding.")
        sys.exit(1)
    else:
        print("\n🎉 Happy learning with AWS Wrangler!")
        sys.exit(0) 