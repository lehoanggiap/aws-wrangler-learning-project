"""
FastAPI Application - Demonstrates AWS Wrangler data loading
Simulates the news API system with S3 data integration
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks, Query
from fastapi.responses import JSONResponse
import awswrangler as wr
import pandas as pd
import yaml
import boto3
from datetime import datetime, timedelta
import asyncio
import sqlite3
import os
from typing import Optional, List
import logging
import uvicorn
from contextlib import asynccontextmanager
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global variables for in-memory data
news_data = None
last_refresh = None
config = None
aws_session = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    logger.info("Starting AWS Wrangler News API Demo...")
    
    # Load configuration
    load_config()
    
    # Setup AWS session
    if not setup_aws_session():
        logger.warning("AWS session setup failed, using local data only")
    
    # Setup database
    setup_database()
    
    # Load initial data
    success = await load_news_data_from_s3()
    if not success:
        logger.warning("Failed to load data, some endpoints may not work")
    
    # Start background tasks
    if aws_session:
        print('Starting background tasks')
        asyncio.create_task(background_data_refresh())
        asyncio.create_task(background_db_sync())
    
    logger.info("Application startup completed")
    
    yield
    
    # Shutdown (if needed)
    logger.info("Application shutting down...")

app = FastAPI(
    title="AWS Wrangler News API Demo",
    description="Learning project demonstrating AWS Wrangler operations",
    version="1.0.0",
    lifespan=lifespan
)

def load_config():
    """Load configuration from config.yaml"""
    global config
    with open('config.yaml', 'r') as file:
        config = yaml.safe_load(file)
    return config

def setup_aws_session():
    """Setup AWS session for data operations"""
    global aws_session
    try:
        # Get AWS credentials from environment variables
        aws_access_key_id = os.getenv('AWS_ACCESS_KEY_ID')
        aws_secret_access_key = os.getenv('AWS_SECRET_ACCESS_KEY')
        aws_region = os.getenv('AWS_DEFAULT_REGION', config['aws']['region'])

        print(f"AWS Access Key ID: {aws_access_key_id}")
        print(f"AWS Secret Access Key: {aws_secret_access_key}")
        print(f"AWS Region: {aws_region}")
        
        # Create session with explicit credentials
        if aws_access_key_id and aws_secret_access_key:
            aws_session = boto3.Session(
                aws_access_key_id=aws_access_key_id,
                aws_secret_access_key=aws_secret_access_key,
                region_name=aws_region
            )
            logger.info("AWS session initialized with environment credentials")
        else:
            # Fallback to default credential chain
            aws_session = boto3.Session(region_name=aws_region)
            logger.info("AWS session initialized with default credentials")
        
        # Test the session by listing S3 buckets
        s3_client = aws_session.client('s3')
        s3_client.list_buckets()
        logger.info("AWS credentials validated successfully")
        
        return True
    except Exception as e:
        logger.error(f"Failed to setup AWS session: {e}")
        return False

def setup_database():
    """Initialize SQLite database for user management"""
    db_path = config['database']['sqlite_path']
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP
        )
    ''')
    
    # Create sample users
    sample_users = [
        ('demo_user', 'demo@example.com'),
        ('test_user', 'test@example.com'),
        ('admin', 'admin@example.com')
    ]
    
    for username, email in sample_users:
        cursor.execute(
            'INSERT OR IGNORE INTO users (username, email) VALUES (?, ?)',
            (username, email)
        )
    
    conn.commit()
    conn.close()
    logger.info("Database initialized successfully")

async def load_news_data_from_s3():
    """Load news data from S3 using AWS Wrangler"""
    global news_data, last_refresh
    
    try:
        bucket = config['aws']['s3_bucket']
        s3_path = f"s3://{bucket}/{config['s3_paths']['news_parquet']}"
        
        logger.info(f"Loading data from S3: {s3_path}")
        
        # Load data using AWS Wrangler
        df = wr.s3.read_parquet(s3_path, boto3_session=aws_session)
        
        # Data preprocessing
        df['art2_date'] = pd.to_datetime(df['art2_date'])
        df = df.sort_values('art2_date', ascending=False)
        
        news_data = df
        last_refresh = datetime.now()
        
        logger.info(f"Successfully loaded {len(df)} articles from S3")
        return True
        
    except Exception as e:
        logger.error(f"Failed to load data from S3: {e}")
        # Fallback to local data if S3 fails
        return await load_news_data_local()

async def load_news_data_local():
    """Fallback: Load news data from local file"""
    global news_data, last_refresh
    
    try:
        local_path = 'data/df_all_news.parquet'
        if os.path.exists(local_path):
            df = pd.read_parquet(local_path)
            df['art2_date'] = pd.to_datetime(df['art2_date'])
            df = df.sort_values('art2_date', ascending=False)
            
            news_data = df
            last_refresh = datetime.now()
            
            logger.info(f"Loaded {len(df)} articles from local file")
            return True
        else:
            logger.error("No local data file found")
            return False
            
    except Exception as e:
        logger.error(f"Failed to load local data: {e}")
        return False

async def sync_database_to_s3():
    """Sync SQLite database to S3 using AWS Wrangler"""
    try:
        # Read users from SQLite
        db_path = config['database']['sqlite_path']
        conn = sqlite3.connect(db_path)
        users_df = pd.read_sql_query("SELECT * FROM users", conn)
        conn.close()
        
        # Export to S3
        bucket = config['aws']['s3_bucket']
        s3_path = f"s3://{bucket}/{config['s3_paths']['db_backup']}users_{datetime.now().strftime('%Y%m%d_%H%M%S')}.parquet"
        
        wr.s3.to_parquet(
            df=users_df,
            path=s3_path,
            boto3_session=aws_session
        )
        
        logger.info(f"Database synced to S3: {s3_path}")
        
    except Exception as e:
        logger.error(f"Database sync failed: {e}")

async def background_data_refresh():
    """Background task to refresh data periodically"""
    while True:
        try:
            await asyncio.sleep(config['background_tasks']['data_refresh_interval'])
            logger.info("Starting background data refresh...")
            await load_news_data_from_s3()
        except Exception as e:
            logger.error(f"Background refresh failed: {e}")
            break

async def background_db_sync():
    """Background task to sync database periodically"""
    while True:
        try:
            await asyncio.sleep(config['background_tasks']['db_sync_interval'])
            logger.info("Starting background database sync...")
            await sync_database_to_s3()
        except Exception as e:
            logger.error(f"Background sync failed: {e}")
            break

@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "AWS Wrangler News API Demo",
        "version": "1.0.0",
        "description": "Learning project for AWS Wrangler operations",
        "endpoints": {
            "health": "/health",
            "news": "/news",
            "companies": "/companies",
            "categories": "/categories",
            "stats": "/stats"
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    global news_data, last_refresh
    
    return {
        "status": "healthy",
        "data_loaded": news_data is not None,
        "total_articles": len(news_data) if news_data is not None else 0,
        "last_refresh": last_refresh.isoformat() if last_refresh else None,
        "aws_session": aws_session is not None
    }

@app.get("/news")
async def get_news(
    company: Optional[str] = Query(None, description="Filter by company name"),
    category: Optional[str] = Query(None, description="Filter by category"),
    limit: int = Query(10, ge=1, le=100, description="Number of articles to return"),
    days: int = Query(30, ge=1, le=365, description="Articles from last N days")
):
    """Get news articles with filtering options"""
    global news_data
    
    if news_data is None:
        raise HTTPException(status_code=503, detail="Data not available")
    
    # Start with all data
    filtered_data = news_data.copy()
    
    # Apply date filter
    cutoff_date = datetime.now() - timedelta(days=days)
    filtered_data = filtered_data[filtered_data['art2_date'] >= cutoff_date]
    
    # Apply company filter
    if company:
        filtered_data = filtered_data[
            filtered_data['company_name'].str.contains(company, case=False, na=False)
        ]
    
    # Apply category filter
    if category:
        filtered_data = filtered_data[
            filtered_data['category'].str.contains(category, case=False, na=False)
        ]
    
    # Limit results
    filtered_data = filtered_data.head(limit)
    
    # Convert to JSON-serializable format
    articles = []
    for _, row in filtered_data.iterrows():
        articles.append({
            "id": int(row['id']),
            "title": row['art2_title'],
            "content": row['art2_content'][:200] + "..." if len(row['art2_content']) > 200 else row['art2_content'],
            "company": row['company_name'],
            "category": row['category'],
            "date": row['art2_date'].isoformat(),
            "sentiment": float(row['sentiment_score']),
            "url": row['art2_url']
        })
    
    return {
        "articles": articles,
        "total_found": len(filtered_data),
        "filters_applied": {
            "company": company,
            "category": category,
            "days": days,
            "limit": limit
        }
    }

@app.get("/companies")
async def get_companies():
    """Get list of all companies in the dataset"""
    global news_data
    
    if news_data is None:
        raise HTTPException(status_code=503, detail="Data not available")
    
    companies = news_data['company_name'].value_counts().to_dict()
    
    return {
        "companies": companies,
        "total_companies": len(companies)
    }

@app.get("/categories")
async def get_categories():
    """Get list of all categories in the dataset"""
    global news_data
    
    if news_data is None:
        raise HTTPException(status_code=503, detail="Data not available")
    
    categories = news_data['category'].value_counts().to_dict()
    
    return {
        "categories": categories,
        "total_categories": len(categories)
    }

@app.get("/stats")
async def get_statistics():
    """Get dataset statistics"""
    global news_data, last_refresh
    
    if news_data is None:
        raise HTTPException(status_code=503, detail="Data not available")
    
    # Calculate statistics
    total_articles = len(news_data)
    date_range = {
        "earliest": news_data['art2_date'].min().isoformat(),
        "latest": news_data['art2_date'].max().isoformat()
    }
    
    sentiment_stats = {
        "average": float(news_data['sentiment_score'].mean()),
        "min": float(news_data['sentiment_score'].min()),
        "max": float(news_data['sentiment_score'].max())
    }
    
    # Recent activity (last 7 days)
    recent_cutoff = datetime.now() - timedelta(days=7)
    recent_articles = len(news_data[news_data['art2_date'] >= recent_cutoff])
    
    return {
        "total_articles": total_articles,
        "date_range": date_range,
        "sentiment_statistics": sentiment_stats,
        "recent_articles_7_days": recent_articles,
        "last_refresh": last_refresh.isoformat() if last_refresh else None,
        "data_source": "S3" if aws_session else "Local"
    }

@app.post("/refresh")
async def manual_refresh(background_tasks: BackgroundTasks):
    """Manually trigger data refresh from S3"""
    if not aws_session:
        raise HTTPException(status_code=503, detail="AWS session not available")
    
    background_tasks.add_task(load_news_data_from_s3)
    
    return {
        "message": "Data refresh initiated",
        "status": "processing"
    }

@app.get("/users")
async def get_users():
    """Get list of users from SQLite database"""
    try:
        db_path = config['database']['sqlite_path']
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT id, username, email, created_at, last_login FROM users")
        users = cursor.fetchall()
        conn.close()
        
        user_list = []
        for user in users:
            user_list.append({
                "id": user[0],
                "username": user[1],
                "email": user[2],
                "created_at": user[3],
                "last_login": user[4]
            })
        
        return {
            "users": user_list,
            "total_users": len(user_list)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

if __name__ == "__main__":
    print('Run the app')
    uvicorn.run(
        app, 
        host=config['api']['host'] if config else "0.0.0.0",
        port=config['api']['port'] if config else 8000
    ) 