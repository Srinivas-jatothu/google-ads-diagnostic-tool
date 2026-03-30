-- ============================================================================
-- GOOGLE ADS DIAGNOSTIC TOOL - SQL ANALYTICS QUERIES
-- ============================================================================
-- Author: Jatothu Srinivas Nayak
-- Purpose: Advanced SQL queries for campaign analysis and troubleshooting
-- Database: SQLite
-- ============================================================================

-- ----------------------------------------------------------------------------
-- 1. CAMPAIGN PERFORMANCE OVERVIEW
-- ----------------------------------------------------------------------------
-- Get comprehensive performance metrics for all campaigns (last 30 days)
SELECT 
    campaign_id,
    campaign_name,
    SUM(impressions) as total_impressions,
    SUM(clicks) as total_clicks,
    SUM(conversions) as total_conversions,
    ROUND(AVG(ctr), 2) as avg_ctr,
    ROUND(AVG(roas), 2) as avg_roas,
    ROUND(AVG(conversion_rate), 2) as avg_cvr,
    ROUND(SUM(cost), 2) as total_spend,
    ROUND(SUM(revenue), 2) as total_revenue,
    ROUND(SUM(revenue) - SUM(cost), 2) as profit
FROM campaigns
WHERE date >= date('now', '-30 days')
GROUP BY campaign_id, campaign_name
ORDER BY total_spend DESC;

-- ----------------------------------------------------------------------------
-- 2. DAILY PERFORMANCE TRENDS
-- ----------------------------------------------------------------------------
-- Analyze day-by-day performance patterns
SELECT 
    date,
    SUM(impressions) as daily_impressions,
    SUM(clicks) as daily_clicks,
    SUM(conversions) as daily_conversions,
    ROUND(SUM(clicks) * 100.0 / SUM(impressions), 2) as daily_ctr,
    ROUND(SUM(conversions) * 100.0 / SUM(clicks), 2) as daily_cvr,
    ROUND(SUM(cost), 2) as daily_spend,
    ROUND(SUM(revenue), 2) as daily_revenue
FROM campaigns
WHERE date >= date('now', '-30 days')
GROUP BY date
ORDER BY date DESC;

-- ----------------------------------------------------------------------------
-- 3. UNDERPERFORMING CAMPAIGNS (TROUBLESHOOTING)
-- ----------------------------------------------------------------------------
-- Identify campaigns with performance issues
SELECT 
    campaign_id,
    campaign_name,
    ROUND(AVG(ctr), 2) as avg_ctr,
    ROUND(AVG(roas), 2) as avg_roas,
    ROUND(AVG(conversion_rate), 2) as avg_cvr,
    ROUND(SUM(cost), 2) as total_spend,
    CASE 
        WHEN AVG(ctr) < 1.0 THEN 'Critical: Very Low CTR'
        WHEN AVG(ctr) < 1.5 THEN 'Warning: Low CTR'
        WHEN AVG(roas) < 1.5 THEN 'Critical: Unprofitable ROAS'
        WHEN AVG(roas) < 2.0 THEN 'Warning: Low ROAS'
        WHEN AVG(conversion_rate) < 1.5 THEN 'Warning: Low Conversion Rate'
        ELSE 'Healthy'
    END as diagnosis,
    CASE 
        WHEN AVG(ctr) < 1.0 THEN 'Immediate action: Review ad copy and targeting'
        WHEN AVG(roas) < 1.5 THEN 'Immediate action: Reduce bids or pause'
        WHEN AVG(roas) < 2.0 THEN 'Monitor closely and optimize'
        ELSE 'Continue monitoring'
    END as recommendation
FROM campaigns
WHERE date >= date('now', '-7 days')
GROUP BY campaign_id, campaign_name
HAVING AVG(ctr) < 1.5 OR AVG(roas) < 2.0 OR AVG(conversion_rate) < 2.0
ORDER BY avg_roas ASC;

-- ----------------------------------------------------------------------------
-- 4. TOP PERFORMERS vs WORST PERFORMERS
-- ----------------------------------------------------------------------------
-- Compare best and worst campaigns side by side
WITH ranked_campaigns AS (
    SELECT 
        campaign_id,
        campaign_name,
        ROUND(AVG(roas), 2) as avg_roas,
        ROUND(SUM(cost), 2) as total_spend,
        ROW_NUMBER() OVER (ORDER BY AVG(roas) DESC) as rank_best,
        ROW_NUMBER() OVER (ORDER BY AVG(roas) ASC) as rank_worst
    FROM campaigns
    WHERE date >= date('now', '-7 days')
    GROUP BY campaign_id, campaign_name
)
SELECT 
    campaign_name,
    avg_roas,
    total_spend,
    CASE 
        WHEN rank_best <= 3 THEN 'Top Performer'
        WHEN rank_worst <= 3 THEN 'Needs Improvement'
    END as category
FROM ranked_campaigns
WHERE rank_best <= 3 OR rank_worst <= 3
ORDER BY avg_roas DESC;

-- ----------------------------------------------------------------------------
-- 5. WEEKEND vs WEEKDAY PERFORMANCE
-- ----------------------------------------------------------------------------
-- Analyze performance patterns by day of week
SELECT 
    CASE 
        WHEN CAST(strftime('%w', date) AS INTEGER) IN (0, 6) THEN 'Weekend'
        ELSE 'Weekday'
    END as day_type,
    COUNT(DISTINCT date) as num_days,
    ROUND(AVG(impressions), 0) as avg_impressions,
    ROUND(AVG(clicks), 0) as avg_clicks,
    ROUND(AVG(conversions), 0) as avg_conversions,
    ROUND(AVG(ctr), 2) as avg_ctr,
    ROUND(AVG(roas), 2) as avg_roas,
    ROUND(AVG(cost), 2) as avg_daily_spend
FROM campaigns
WHERE date >= date('now', '-30 days')
GROUP BY day_type;

-- ----------------------------------------------------------------------------
-- 6. CAMPAIGN EFFICIENCY METRICS
-- ----------------------------------------------------------------------------
-- Calculate cost-per-action metrics
SELECT 
    campaign_id,
    campaign_name,
    ROUND(SUM(cost) / SUM(clicks), 2) as cpc,
    ROUND(SUM(cost) / SUM(conversions), 2) as cpa,
    ROUND(SUM(revenue) / SUM(conversions), 2) as revenue_per_conversion,
    ROUND((SUM(revenue) - SUM(cost)) / SUM(conversions), 2) as profit_per_conversion,
    SUM(conversions) as total_conversions
FROM campaigns
WHERE date >= date('now', '-30 days')
  AND conversions > 0
GROUP BY campaign_id, campaign_name
ORDER BY profit_per_conversion DESC;

-- ----------------------------------------------------------------------------
-- 7. TREND ANALYSIS WITH LAG FUNCTIONS
-- ----------------------------------------------------------------------------
-- Compare each day's performance to previous day
SELECT 
    date,
    campaign_id,
    clicks,
    conversions,
    cost,
    LAG(clicks, 1) OVER (PARTITION BY campaign_id ORDER BY date) as prev_day_clicks,
    LAG(conversions, 1) OVER (PARTITION BY campaign_id ORDER BY date) as prev_day_conversions,
    ROUND(
        (clicks - LAG(clicks, 1) OVER (PARTITION BY campaign_id ORDER BY date)) * 100.0 / 
        NULLIF(LAG(clicks, 1) OVER (PARTITION BY campaign_id ORDER BY date), 0), 
        2
    ) as clicks_pct_change,
    ROUND(
        (conversions - LAG(conversions, 1) OVER (PARTITION BY campaign_id ORDER BY date)) * 100.0 / 
        NULLIF(LAG(conversions, 1) OVER (PARTITION BY campaign_id ORDER BY date), 0), 
        2
    ) as conversions_pct_change
FROM campaigns
WHERE date >= date('now', '-14 days')
ORDER BY campaign_id, date DESC;

-- ----------------------------------------------------------------------------
-- 8. ZERO CONVERSION CAMPAIGNS (HIGH PRIORITY ISSUES)
-- ----------------------------------------------------------------------------
-- Find campaigns spending money without generating conversions
SELECT 
    campaign_id,
    campaign_name,
    SUM(impressions) as total_impressions,
    SUM(clicks) as total_clicks,
    SUM(conversions) as total_conversions,
    ROUND(SUM(cost), 2) as wasted_spend,
    COUNT(*) as days_with_zero_conversions
FROM campaigns
WHERE date >= date('now', '-7 days')
GROUP BY campaign_id, campaign_name
HAVING SUM(conversions) = 0 AND SUM(cost) > 100
ORDER BY wasted_spend DESC;

-- ----------------------------------------------------------------------------
-- 9. CAMPAIGN HEALTH SCORE
-- ----------------------------------------------------------------------------
-- Create a composite health score (0-100) for each campaign
SELECT 
    campaign_id,
    campaign_name,
    ROUND(AVG(ctr), 2) as avg_ctr,
    ROUND(AVG(roas), 2) as avg_roas,
    ROUND(AVG(conversion_rate), 2) as avg_cvr,
    ROUND(
        (
            (CASE WHEN AVG(ctr) >= 2.5 THEN 40 WHEN AVG(ctr) >= 1.5 THEN 25 ELSE 10 END) +
            (CASE WHEN AVG(roas) >= 4.0 THEN 40 WHEN AVG(roas) >= 2.5 THEN 25 ELSE 10 END) +
            (CASE WHEN AVG(conversion_rate) >= 3.0 THEN 20 WHEN AVG(conversion_rate) >= 2.0 THEN 12 ELSE 5 END)
        ), 0
    ) as health_score,
    CASE 
        WHEN (
            (CASE WHEN AVG(ctr) >= 2.5 THEN 40 WHEN AVG(ctr) >= 1.5 THEN 25 ELSE 10 END) +
            (CASE WHEN AVG(roas) >= 4.0 THEN 40 WHEN AVG(roas) >= 2.5 THEN 25 ELSE 10 END) +
            (CASE WHEN AVG(conversion_rate) >= 3.0 THEN 20 WHEN AVG(conversion_rate) >= 2.0 THEN 12 ELSE 5 END)
        ) >= 75 THEN 'Excellent'
        WHEN (
            (CASE WHEN AVG(ctr) >= 2.5 THEN 40 WHEN AVG(ctr) >= 1.5 THEN 25 ELSE 10 END) +
            (CASE WHEN AVG(roas) >= 4.0 THEN 40 WHEN AVG(roas) >= 2.5 THEN 25 ELSE 10 END) +
            (CASE WHEN AVG(conversion_rate) >= 3.0 THEN 20 WHEN AVG(conversion_rate) >= 2.0 THEN 12 ELSE 5 END)
        ) >= 50 THEN 'Good'
        ELSE 'Needs Improvement'
    END as health_status
FROM campaigns
WHERE date >= date('now', '-7 days')
GROUP BY campaign_id, campaign_name
ORDER BY health_score DESC;

-- ----------------------------------------------------------------------------
-- 10. CUMULATIVE METRICS
-- ----------------------------------------------------------------------------
-- Running totals for spend and revenue
SELECT 
    date,
    SUM(cost) OVER (ORDER BY date) as cumulative_spend,
    SUM(revenue) OVER (ORDER BY date) as cumulative_revenue,
    SUM(revenue - cost) OVER (ORDER BY date) as cumulative_profit
FROM (
    SELECT 
        date,
        SUM(cost) as cost,
        SUM(revenue) as revenue
    FROM campaigns
    WHERE date >= date('now', '-30 days')
    GROUP BY date
)
ORDER BY date;