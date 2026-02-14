"""
Cleanup Worker
Performs periodic maintenance tasks
"""

from celery import shared_task
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


@shared_task(name='backend.workers.cleanup.clean_expired_sessions')
def clean_expired_sessions():
    """
    Clean expired user sessions
    
    Runs every 6 hours to remove old sessions
    """
    from backend.engines.db_engine import get_conn
    
    try:
        conn = get_conn()
        cursor = conn.cursor()
        
        # Delete sessions older than 24 hours
        cutoff = datetime.now() - timedelta(hours=24)
        
        cursor.execute("""
            DELETE FROM sessions
            WHERE updated_at < ?
        """, (cutoff,))
        
        deleted = cursor.rowcount
        conn.commit()
        conn.close()
        
        logger.info(f"🗑️ Cleaned {deleted} expired sessions")
        return {"deleted": deleted}
    
    except Exception as e:
        logger.error(f"❌ Session cleanup failed: {e}")
        return {"error": str(e)}


@shared_task(name='backend.workers.cleanup.clean_old_webhook_events')
def clean_old_webhook_events(days: int = 30):
    """
    Clean old webhook events (keep last 30 days)
    
    Args:
        days: Number of days to keep
    """
    from backend.engines.db_engine import get_conn
    
    try:
        cutoff = datetime.now() - timedelta(days=days)
        
        conn = get_conn()
        cursor = conn.cursor()
        
        # Keep only successful events from last 30 days
        # Keep all failed events for debugging
        cursor.execute("""
            DELETE FROM webhook_events
            WHERE status = 'COMPLETED'
            AND created_at < ?
        """, (cutoff,))
        
        deleted = cursor.rowcount
        conn.commit()
        conn.close()
        
        logger.info(f"🗑️ Cleaned {deleted} old webhook events")
        return {"deleted": deleted}
    
    except Exception as e:
        logger.error(f"❌ Webhook cleanup failed: {e}")
        return {"error": str(e)}


@shared_task(name='backend.workers.cleanup.vacuum_database')
def vacuum_database():
    """
    Vacuum SQLite database to reclaim space
    
    Runs weekly to optimize database
    """
    from backend.engines.db_engine import get_conn
    
    try:
        conn = get_conn()
        
        # VACUUM can't run in a transaction
        conn.isolation_level = None
        cursor = conn.cursor()
        cursor.execute("VACUUM")
        cursor.execute("ANALYZE")
        
        conn.close()
        
        logger.info("🔧 Database vacuumed and analyzed")
        return {"success": True}
    
    except Exception as e:
        logger.error(f"❌ Database vacuum failed: {e}")
        return {"error": str(e)}