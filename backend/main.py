from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import sqlite3
from datetime import datetime, timedelta
from typing import List, Dict

app = FastAPI(
    title="Google Ads Diagnostic Tool",
    description="Automated diagnostics and analytics for Google Ads campaigns",
    version="1.0.0"
)

# CORS middleware for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db_connection():
    """Get database connection"""
    return sqlite3.connect('ads_data.db')

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "online",
        "message": "Google Ads Diagnostic Tool API",
        "version": "1.0.0"
    }

@app.get("/api/dashboard")
async def get_dashboard_metrics():
    """Get overall dashboard metrics for last 7 days"""
    conn = get_db_connection()
    
    query = """
    SELECT 
        SUM(impressions) as total_impressions,
        SUM(clicks) as total_clicks,
        SUM(conversions) as total_conversions,
        ROUND(SUM(cost), 2) as total_cost,
        ROUND(SUM(revenue), 2) as total_revenue,
        ROUND(AVG(ctr), 2) as avg_ctr,
        ROUND(AVG(roas), 2) as avg_roas,
        ROUND(AVG(conversion_rate), 2) as avg_conversion_rate,
        COUNT(DISTINCT campaign_id) as active_campaigns
    FROM campaigns
    WHERE date >= date('now', '-7 days')
    """
    
    result = pd.read_sql(query, conn)
    conn.close()
    
    metrics = result.to_dict('records')[0]
    
    # Calculate derived metrics
    if metrics['total_cost'] and metrics['total_cost'] > 0:
        metrics['profit'] = round(metrics['total_revenue'] - metrics['total_cost'], 2)
        metrics['roi_percentage'] = round((metrics['profit'] / metrics['total_cost']) * 100, 2)
    else:
        metrics['profit'] = 0
        metrics['roi_percentage'] = 0
    
    return metrics

@app.get("/api/campaigns/performance")
async def get_campaign_performance():
    """Get top campaigns by performance"""
    conn = get_db_connection()
    
    query = """
    SELECT 
        campaign_id,
        campaign_name,
        SUM(impressions) as impressions,
        SUM(clicks) as clicks,
        SUM(conversions) as conversions,
        ROUND(AVG(ctr), 2) as avg_ctr,
        ROUND(AVG(roas), 2) as avg_roas,
        ROUND(SUM(cost), 2) as total_cost,
        ROUND(SUM(revenue), 2) as total_revenue
    FROM campaigns
    WHERE date >= date('now', '-7 days')
    GROUP BY campaign_id, campaign_name
    ORDER BY total_cost DESC
    LIMIT 10
    """
    
    data = pd.read_sql(query, conn)
    conn.close()
    
    return data.to_dict('records')

@app.get("/api/diagnostics")
async def run_automated_diagnostics():
    """Run automated diagnostics to identify issues"""
    conn = get_db_connection()
    
    issues = []
    
    # Issue 1: Low CTR campaigns
    low_ctr_query = """
    SELECT 
        campaign_id,
        campaign_name,
        ROUND(AVG(ctr), 2) as avg_ctr,
        SUM(impressions) as impressions,
        SUM(clicks) as clicks
    FROM campaigns
    WHERE date >= date('now', '-7 days')
    GROUP BY campaign_id, campaign_name
    HAVING AVG(ctr) < 1.5
    """
    
    low_ctr = pd.read_sql(low_ctr_query, conn)
    
    for _, row in low_ctr.iterrows():
        issues.append({
            'campaign_id': row['campaign_id'],
            'campaign_name': row['campaign_name'],
            'issue_type': 'Low Click-Through Rate',
            'severity': 'High',
            'metric_name': 'CTR',
            'metric_value': f"{row['avg_ctr']}%",
            'threshold': '1.5%',
            'recommendation': 'Review ad copy relevance and targeting. Consider A/B testing new ad creatives.',
            'impact': f"{int(row['impressions']):,} impressions with only {int(row['clicks']):,} clicks"
        })
    
    # Issue 2: Low ROAS campaigns
    low_roas_query = """
    SELECT 
        campaign_id,
        campaign_name,
        ROUND(AVG(roas), 2) as avg_roas,
        ROUND(SUM(cost), 2) as total_cost,
        ROUND(SUM(revenue), 2) as total_revenue
    FROM campaigns
    WHERE date >= date('now', '-7 days')
    GROUP BY campaign_id, campaign_name
    HAVING AVG(roas) < 2.0
    """
    
    low_roas = pd.read_sql(low_roas_query, conn)
    
    for _, row in low_roas.iterrows():
        issues.append({
            'campaign_id': row['campaign_id'],
            'campaign_name': row['campaign_name'],
            'issue_type': 'Low Return on Ad Spend',
            'severity': 'Critical',
            'metric_name': 'ROAS',
            'metric_value': f"{row['avg_roas']}x",
            'threshold': '2.0x',
            'recommendation': 'Reduce bids or pause campaign. Cost exceeds revenue targets.',
            'impact': f"Spent ${row['total_cost']:,.2f}, earned ${row['total_revenue']:,.2f}"
        })
    
    # Issue 3: Low conversion rate
    low_cvr_query = """
    SELECT 
        campaign_id,
        campaign_name,
        ROUND(AVG(conversion_rate), 2) as avg_cvr,
        SUM(clicks) as clicks,
        SUM(conversions) as conversions
    FROM campaigns
    WHERE date >= date('now', '-7 days')
    GROUP BY campaign_id, campaign_name
    HAVING AVG(conversion_rate) < 2.0
    """
    
    low_cvr = pd.read_sql(low_cvr_query, conn)
    
    for _, row in low_cvr.iterrows():
        issues.append({
            'campaign_id': row['campaign_id'],
            'campaign_name': row['campaign_name'],
            'issue_type': 'Low Conversion Rate',
            'severity': 'Medium',
            'metric_name': 'Conversion Rate',
            'metric_value': f"{row['avg_cvr']}%",
            'threshold': '2.0%',
            'recommendation': 'Check landing page experience and offer relevance. Review audience targeting.',
            'impact': f"{int(row['clicks']):,} clicks with only {int(row['conversions']):,} conversions"
        })
    
    # Issue 4: High cost campaigns with no conversions
    no_conversions_query = """
    SELECT 
        campaign_id,
        campaign_name,
        SUM(conversions) as total_conversions,
        ROUND(SUM(cost), 2) as total_cost
    FROM campaigns
    WHERE date >= date('now', '-7 days')
    GROUP BY campaign_id, campaign_name
    HAVING SUM(conversions) = 0 AND SUM(cost) > 500
    """
    
    no_conversions = pd.read_sql(no_conversions_query, conn)
    
    for _, row in no_conversions.iterrows():
        issues.append({
            'campaign_id': row['campaign_id'],
            'campaign_name': row['campaign_name'],
            'issue_type': 'Zero Conversions - High Spend',
            'severity': 'Critical',
            'metric_name': 'Conversions',
            'metric_value': '0',
            'threshold': '> 0',
            'recommendation': 'Pause campaign immediately. Investigate conversion tracking and landing page issues.',
            'impact': f"${row['total_cost']:,.2f} spent with zero conversions"
        })
    
    conn.close()
    
    return {
        'total_issues': len(issues),
        'critical': len([i for i in issues if i['severity'] == 'Critical']),
        'high': len([i for i in issues if i['severity'] == 'High']),
        'medium': len([i for i in issues if i['severity'] == 'Medium']),
        'issues': issues
    }

@app.get("/api/trends")
async def get_performance_trends():
    """Get daily performance trends for last 30 days"""
    conn = get_db_connection()
    
    query = """
    SELECT 
        date,
        SUM(impressions) as impressions,
        SUM(clicks) as clicks,
        SUM(conversions) as conversions,
        ROUND(SUM(cost), 2) as cost,
        ROUND(SUM(revenue), 2) as revenue,
        ROUND(AVG(ctr), 2) as avg_ctr,
        ROUND(AVG(roas), 2) as avg_roas
    FROM campaigns
    WHERE date >= date('now', '-30 days')
    GROUP BY date
    ORDER BY date ASC
    """
    
    data = pd.read_sql(query, conn)
    conn.close()
    
    return data.to_dict('records')

@app.get("/api/campaigns/{campaign_id}")
async def get_campaign_details(campaign_id: str):
    """Get detailed metrics for a specific campaign"""
    conn = get_db_connection()
    
    query = """
    SELECT *
    FROM campaigns
    WHERE campaign_id = ?
    ORDER BY date DESC
    LIMIT 30
    """
    
    data = pd.read_sql(query, conn, params=[campaign_id])
    conn.close()
    
    if data.empty:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    return data.to_dict('records')

@app.get("/api/stats")
async def get_database_stats():
    """Get database statistics"""
    conn = get_db_connection()
    
    stats_query = """
    SELECT 
        COUNT(*) as total_rows,
        COUNT(DISTINCT campaign_id) as total_campaigns,
        MIN(date) as earliest_date,
        MAX(date) as latest_date,
        ROUND(SUM(cost), 2) as total_spend,
        ROUND(SUM(revenue), 2) as total_revenue
    FROM campaigns
    """
    
    stats = pd.read_sql(stats_query, conn)
    conn.close()
    
    return stats.to_dict('records')[0]

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting Google Ads Diagnostic Tool API...")
    print("📊 Dashboard: http://localhost:8000")
    print("📖 API Docs: http://localhost:8000/docs")
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)