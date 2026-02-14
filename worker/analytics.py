"""
Analytics Worker
Generates scheduled analytics reports
"""

from celery import shared_task
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


@shared_task(name='backend.workers.analytics.generate_daily_report')
def generate_daily_report():
    """
    Generate daily revenue report
    
    Runs every day at 9 AM to:
    1. Calculate yesterday's revenue
    2. Compare with previous day
    3. Generate summary
    4. Send to admin (future: via email/Slack)
    
    Returns:
        dict: Report data
    """
    logger.info("📊 Generating daily revenue report...")
    
    from backend.services.analytics.analytics_service import get_analytics_service
    
    try:
        analytics = get_analytics_service()
        
        # Get yesterday's data
        yesterday = datetime.now() - timedelta(days=1)
        revenue_data = analytics.get_revenue_summary(days=1)
        
        # Get last 7 days for comparison
        week_data = analytics.get_revenue_summary(days=7)
        
        # Calculate MRR
        mrr = analytics.get_mrr()
        
        # Get conversion funnel
        funnel = analytics.get_conversion_funnel()
        
        report = {
            "date": yesterday.strftime("%Y-%m-%d"),
            "yesterday_revenue": revenue_data.get("total_revenue", 0),
            "yesterday_orders": revenue_data.get("order_count", 0),
            "week_avg_revenue": week_data.get("total_revenue", 0) / 7,
            "mrr": mrr,
            "conversion_rate": funnel.get("conversion_rate", 0),
            "success_rate": funnel.get("success_rate", 0)
        }
        
        logger.info(f"✅ Daily report generated: ₹{report['yesterday_revenue']:,.2f}")
        
        # TODO: Send report via email/Slack
        _save_report(report)
        
        return report
    
    except Exception as e:
        logger.error(f"❌ Failed to generate daily report: {e}", exc_info=True)
        return {"error": str(e)}


def _save_report(report: dict):
    """Save report to database"""
    from backend.engines.db_engine import get_conn
    import json
    
    try:
        conn = get_conn()
        cursor = conn.cursor()
        
        # Create reports table if not exists
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS daily_reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                report_date DATE NOT NULL UNIQUE,
                revenue REAL,
                orders INTEGER,
                mrr REAL,
                conversion_rate REAL,
                full_report TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Insert report
        cursor.execute("""
            INSERT OR REPLACE INTO daily_reports 
            (report_date, revenue, orders, mrr, conversion_rate, full_report)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            report["date"],
            report["yesterday_revenue"],
            report["yesterday_orders"],
            report["mrr"],
            report["conversion_rate"],
            json.dumps(report)
        ))
        
        conn.commit()
        conn.close()
        
        logger.info(f"💾 Report saved to database")
    
    except Exception as e:
        logger.error(f"❌ Failed to save report: {e}")


@shared_task(name='backend.workers.analytics.cleanup_old_reports')
def cleanup_old_reports(days: int = 90):
    """
    Cleanup old reports (keep last 90 days)
    
    Args:
        days: Number of days to keep
    """
    from backend.engines.db_engine import get_conn
    
    try:
        cutoff_date = datetime.now() - timedelta(days=days)
        
        conn = get_conn()
        cursor = conn.cursor()
        
        cursor.execute("""
            DELETE FROM daily_reports
            WHERE report_date < ?
        """, (cutoff_date.strftime("%Y-%m-%d"),))
        
        deleted = cursor.rowcount
        conn.commit()
        conn.close()
        
        logger.info(f"🗑️ Deleted {deleted} old reports")
        return {"deleted": deleted}
    
    except Exception as e:
        logger.error(f"❌ Failed to cleanup reports: {e}")
        return {"error": str(e)}