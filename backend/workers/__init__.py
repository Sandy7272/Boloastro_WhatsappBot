"""
Background workers package
Celery tasks for automated operations
"""

# Import tasks for Celery autodiscovery
try:
    from backend.workers.payment_recovery import (
        recover_abandoned_payments,
        send_payment_reminder
    )
    from backend.workers.payment_retry import (
        retry_failed_payments,
        manual_retry
    )
    from backend.workers.analytics import (
        generate_daily_report,
        cleanup_old_reports
    )
    from backend.workers.cleanup import (
        clean_expired_sessions,
        clean_old_webhook_events,
        vacuum_database
    )
except ImportError:
    # Workers not installed yet, that's okay
    pass

__all__ = []