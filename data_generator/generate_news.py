"""
News Data Generator - Simulates AIGEN data generation
Creates sample news data similar to the actual news API system
"""

import pandas as pd
import numpy as np
from faker import Faker
from datetime import datetime, timedelta
import random
import yaml
import os

fake = Faker()

def load_config():
    """Load configuration from config.yaml"""
    with open('config.yaml', 'r') as file:
        return yaml.safe_load(file)

def generate_news_articles(config):
    """Generate sample news articles similar to the actual system"""
    
    num_articles = config['data_generation']['num_articles']
    companies = config['data_generation']['companies']
    categories = config['data_generation']['categories']
    
    print(f"Generating {num_articles} news articles...")
    
    articles = []
    
    for i in range(num_articles):
        # Generate article data similar to the actual system structure
        company = random.choice(companies)
        category = random.choice(categories)
        
        # Generate realistic news titles
        title_templates = [
            f"{company} Announces New {category} Initiative",
            f"{company} Partners with Industry Leader in {category}",
            f"{company} Reports Strong {category} Growth",
            f"{company} Launches Revolutionary {category} Platform",
            f"{company} Expands {category} Operations Globally"
        ]
        
        article = {
            # URL and metadata (similar to fetchers.py output)
            'url': fake.url(),
            'url_final': fake.url(),
            'source': random.choice(['Google News', 'Bing News', 'PR Newswire', 'Yahoo Finance']),
            
            # Article content (similar to GSE extraction)
            'art_title': random.choice(title_templates),
            'art2_title': random.choice(title_templates),  # Cleaned title
            'art2_text': fake.text(max_nb_chars=2000),
            'art2_date': fake.date_time_between(start_date='-30d', end_date='now'),
            
            # Company and category info (similar to cats.py processing)
            'company_name': company,
            'company_id': f"com_{company.lower().replace(' ', '_')}",
            'category': category,
            'category_score': random.uniform(0.7, 0.99),
            
            # NLP processing results (similar to cats.py output)
            'sentiment_score': random.uniform(-1, 1),
            'sentiment_label': random.choice(['positive', 'negative', 'neutral']),
            'summary': fake.sentence(nb_words=20),
            
            # Processing metadata
            'processed_date': datetime.now(),
            'data_source': 'generated',
            'is_valid': True,
            'priority_score': random.uniform(0, 1)
        }
        
        articles.append(article)
        
        if (i + 1) % 100 == 0:
            print(f"Generated {i + 1} articles...")
    
    df = pd.DataFrame(articles)
    
    # Add some data quality issues to simulate real-world data
    # Some articles with missing data
    missing_indices = np.random.choice(df.index, size=int(len(df) * 0.05), replace=False)
    df.loc[missing_indices, 'art2_text'] = None
    
    # Some duplicate titles
    duplicate_indices = np.random.choice(df.index, size=int(len(df) * 0.02), replace=False)
    df.loc[duplicate_indices, 'art_title'] = df.iloc[0]['art_title']
    
    print(f"Generated {len(df)} articles with realistic data quality issues")
    return df

def save_local_data(df):
    """Save data locally for testing"""
    os.makedirs('data', exist_ok=True)
    
    # Save as parquet (similar to actual system)
    parquet_path = 'data/df_all_news.parquet'
    df.to_parquet(parquet_path, index=False)
    print(f"Saved data locally: {parquet_path}")
    
    # Save as CSV for easy inspection
    csv_path = 'data/df_all_news.csv'
    df.to_csv(csv_path, index=False)
    print(f"Saved data locally: {csv_path}")
    
    return parquet_path

def main():
    """Main function to generate news data"""
    print("=== News Data Generator ===")
    print("Simulating AIGEN data generation process...")
    
    # Load configuration
    config = load_config()
    
    # Generate news articles
    df = generate_news_articles(config)
    
    # Save locally
    parquet_path = save_local_data(df)
    
    # Display summary
    print("\n=== Data Generation Summary ===")
    print(f"Total articles: {len(df)}")
    print(f"Companies: {df['company_name'].nunique()}")
    print(f"Categories: {df['category'].nunique()}")
    print(f"Date range: {df['art2_date'].min()} to {df['art2_date'].max()}")
    print(f"Average sentiment: {df['sentiment_score'].mean():.3f}")
    
    print("\nSample articles:")
    print(df[['art_title', 'company_name', 'category', 'sentiment_label']].head())
    
    print(f"\nData saved to: {parquet_path}")
    print("Next step: Run 'python data_generator/export_to_s3.py' to upload to S3")

if __name__ == "__main__":
    main() 