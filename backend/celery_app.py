"""
Celery Configuration for Background Jobs
Place this file in: backend/celery_app.py (NOT in backend/config/)
"""

from celery import Celery

# Initialize Celery
celery_app = Celery('boloastro')


def configure_celery():
    """Configure celery app"""
    # Import here to avoid circular imports
    from celery.schedules import crontab
    from backend.config import Config
    
    # Celery configuration
    celery_app.conf.update(
        broker_url=Config.CELERY_BROKER_URL,
        result_backend=Config.CELERY_RESULT_BACKEND,
        task_serializer='json',
        accept_content=['json'],
        result_serializer='json',
        timezone='Asia/Kolkata',
        enable_utc=True,
        
        # Task execution settings
        task_time_limit=Config.CELERY_TASK_TIME_LIMIT,
        task_soft_time_limit=Config.CELERY_TASK_SOFT_TIME_LIMIT,
        task_acks_late=True,
        worker_prefetch_multiplier=1,
        
        # Result settings
        result_expires=3600,
        
        # Task routing
        task_routes={
            'backend.workers.payment_recovery.*': {'queue': 'high_priority'},
            'backend.workers.payment_retry.*': {'queue': 'high_priority'},
            'backend.workers.notification.*': {'queue': 'normal'},
            'backend.workers.analytics.*': {'queue': 'low_priority'},
        },
        
        # Beat schedule (periodic tasks)
        beat_schedule={
            'recover-abandoned-payments': {
                'task': 'backend.workers.payment_recovery.recover_abandoned_payments',
                'schedule': crontab(minute=0),
            },
            'retry-failed-payments': {
                'task': 'backend.workers.payment_retry.retry_failed_payments',
                'schedule': crontab(minute=0, hour='*/2'),
            },
            'daily-revenue-report': {
                'task': 'backend.workers.analytics.generate_daily_report',
                'schedule': crontab(hour=9, minute=0),
            },
            'clean-expired-sessions': {
                'task': 'backend.workers.cleanup.clean_expired_sessions',
                'schedule': crontab(minute=0, hour='*/6'),
            },
        },
    )
    
    # Auto-discover tasks
    celery_app.autodiscover_tasks([
        'backend.workers.payment_recovery',
        'backend.workers.payment_retry',
        'backend.workers.analytics',
        'backend.workers.cleanup',
    ])


# Configure on import
configure_celery()


if __name__ == '__main__':
    celery_app.start()