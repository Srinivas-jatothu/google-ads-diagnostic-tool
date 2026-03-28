import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random

def generate_campaign_data():
    """Generate realistic Google Ads campaign data"""
    
    print("🔄 Generating campaign data...")
    
    # Campaign names (realistic Google Ads campaigns)
    campaigns = [
        {'id': 'camp_001', 'name': 'Search - Brand Keywords'},
        {'id': 'camp_002', 'name': 'Display - Remarketing'},
        {'id': 'camp_003', 'name': 'Shopping - Best Sellers'},
        {'id': 'camp_004', 'name': 'Search - Competitor Keywords'},
        {'id': 'camp_005', 'name': 'YouTube - Video Ads'},
        {'id': 'camp_006', 'name': 'Performance Max - Holiday'},
        {'id': 'camp_007', 'name': 'Search - Long Tail'},
        {'id': 'camp_008', 'name': 'Display - Prospecting'},
        {'id': 'camp_009', 'name': 'Search - High Intent'},
        {'id': 'camp_010', 'name': 'Shopping - All Products'},
    ]
    
    # Generate 30 days of data
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)
    
    all_data = []
    
    for campaign in campaigns:
        campaign_id = campaign['id']
        campaign_name = campaign['name']
        
        # Assign performance tier (some campaigns perform better)
        if campaign_id in ['camp_001', 'camp_003', 'camp_009']:
            performance_tier = 'high'
        elif campaign_id in ['camp_004', 'camp_008']:
            performance_tier = 'low'
        else:
            performance_tier = 'medium'
        
        # Generate daily data
        current_date = start_date
        while current_date <= end_date:
            # Weekend boost for some campaigns
            is_weekend = current_date.weekday() >= 5
            weekend_multiplier = 1.3 if is_weekend else 1.0
            
            # Base metrics by performance tier
            if performance_tier == 'high':
                base_impressions = random.randint(20000, 50000)
                base_ctr = random.uniform(2.5, 4.0)  # Good CTR
                base_cvr = random.uniform(3.0, 6.0)  # Good conversion rate
                base_roas = random.uniform(3.5, 6.0)  # Good ROAS
            elif performance_tier == 'low':
                base_impressions = random.randint(15000, 35000)
                base_ctr = random.uniform(0.4, 1.2)  # Poor CTR
                base_cvr = random.uniform(0.5, 1.5)  # Poor conversion rate
                base_roas = random.uniform(0.8, 1.8)  # Poor ROAS
            else:
                base_impressions = random.randint(18000, 40000)
                base_ctr = random.uniform(1.5, 2.5)  # Medium CTR
                base_cvr = random.uniform(2.0, 3.5)  # Medium conversion rate
                base_roas = random.uniform(2.0, 3.5)  # Medium ROAS
            
            # Apply weekend multiplier
            impressions = int(base_impressions * weekend_multiplier)
            
            # Calculate clicks from impressions and CTR
            clicks = int(impressions * (base_ctr / 100))
            
            # Calculate conversions from clicks and conversion rate
            conversions = int(clicks * (base_cvr / 100))
            
            # Calculate cost (CPC varies by campaign type)
            if 'Search' in campaign_name:
                cpc = random.uniform(1.5, 4.0)
            elif 'Shopping' in campaign_name:
                cpc = random.uniform(0.8, 2.0)
            else:
                cpc = random.uniform(0.5, 1.5)
            
            cost = round(clicks * cpc, 2)
            
            # Calculate revenue from ROAS
            revenue = round(cost * base_roas, 2)
            
            # Add some randomness to make it realistic
            impressions = int(impressions * random.uniform(0.9, 1.1))
            clicks = int(clicks * random.uniform(0.9, 1.1))
            conversions = int(conversions * random.uniform(0.85, 1.15))
            
            # Ensure minimum values
            clicks = max(clicks, 10)
            conversions = max(conversions, 0)
            
            # Recalculate actual metrics
            actual_ctr = round((clicks / impressions * 100), 2) if impressions > 0 else 0
            actual_cpc = round((cost / clicks), 2) if clicks > 0 else 0
            actual_roas = round((revenue / cost), 2) if cost > 0 else 0
            actual_cvr = round((conversions / clicks * 100), 2) if clicks > 0 else 0
            
            all_data.append({
                'campaign_id': campaign_id,
                'campaign_name': campaign_name,
                'date': current_date.strftime('%Y-%m-%d'),
                'impressions': impressions,
                'clicks': clicks,
                'conversions': conversions,
                'cost': cost,
                'revenue': revenue,
                'ctr': actual_ctr,
                'cpc': actual_cpc,
                'roas': actual_roas,
                'conversion_rate': actual_cvr
            })
            
            current_date += timedelta(days=1)
    
    # Create DataFrame
    df = pd.DataFrame(all_data)
    
    # Create SQLite database
    conn = sqlite3.connect('ads_data.db')
    df.to_sql('campaigns', conn, if_exists='replace', index=False)
    
    # Create summary table
    summary = df.groupby('campaign_id').agg({
        'campaign_name': 'first',
        'impressions': 'sum',
        'clicks': 'sum',
        'conversions': 'sum',
        'cost': 'sum',
        'revenue': 'sum',
        'ctr': 'mean',
        'roas': 'mean'
    }).reset_index()
    
    summary.to_sql('campaign_summary', conn, if_exists='replace', index=False)
    
    conn.close()
    
    print(f"✅ Generated {len(df)} rows of campaign data")
    print(f"✅ Date range: {df['date'].min()} to {df['date'].max()}")
    print(f"✅ Campaigns: {df['campaign_id'].nunique()}")
    print(f"✅ Database saved to: ads_data.db")
    
    return df

if __name__ == "__main__":
    generate_campaign_data()