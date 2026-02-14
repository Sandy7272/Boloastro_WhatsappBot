"""
Production Database Connection with Connection Pooling
Supports both SQLite (dev) and PostgreSQL (production)
"""

from sqlalchemy import create_engine, event, pool
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.ext.declarative import declarative_base
from contextlib import contextmanager
import logging

logger = logging.getLogger(__name__)

# Base class for all models
Base = declarative_base()


class Database:
    """
    Database connection manager with pooling
    """
    
    def __init__(self, database_url: str, **kwargs):
        """
        Initialize database connection
        
        Args:
            database_url: Database connection string
            **kwargs: Additional SQLAlchemy engine parameters
        """
        self.database_url = database_url
        
        # Default engine parameters
        engine_params = {
            'pool_pre_ping': True,  # Verify connection before use
            'pool_recycle': 3600,   # Recycle connections after 1 hour
            'echo': kwargs.get('echo', False),
        }
        
        # PostgreSQL-specific optimizations
        if database_url.startswith('postgresql'):
            engine_params.update({
                'pool_size': kwargs.get('pool_size', 10),
                'max_overflow': kwargs.get('max_overflow', 20),
                'pool_timeout': kwargs.get('pool_timeout', 30),
            })
        
        # SQLite-specific settings
        elif database_url.startswith('sqlite'):
            engine_params.update({
                'connect_args': {'check_same_thread': False},
                'poolclass': pool.StaticPool,  # Single connection for SQLite
            })
        
        # Create engine
        self.engine = create_engine(database_url, **engine_params)
        
        # Configure connection event listeners
        self._setup_event_listeners()
        
        # Create session factory
        self.SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine
        )
        
        # Thread-safe session
        self.ScopedSession = scoped_session(self.SessionLocal)
        
        logger.info(f"Database initialized: {database_url.split('@')[-1]}")
    
    def _setup_event_listeners(self):
        """Setup database event listeners for monitoring"""
        
        @event.listens_for(self.engine, "connect")
        def receive_connect(dbapi_conn, connection_record):
            logger.debug("Database connection established")
        
        @event.listens_for(self.engine, "checkout")
        def receive_checkout(dbapi_conn, connection_record, connection_proxy):
            logger.debug("Connection checked out from pool")
        
        @event.listens_for(self.engine, "checkin")
        def receive_checkin(dbapi_conn, connection_record):
            logger.debug("Connection returned to pool")
    
    def create_all_tables(self):
        """Create all database tables"""
        Base.metadata.create_all(bind=self.engine)
        logger.info("All database tables created")
    
    def drop_all_tables(self):
        """Drop all database tables (use with caution!)"""
        Base.metadata.drop_all(bind=self.engine)
        logger.warning("All database tables dropped")
    
    def get_session(self):
        """
        Get a new database session
        
        Returns:
            Session: SQLAlchemy session
        """
        return self.SessionLocal()
    
    @contextmanager
    def session_scope(self):
        """
        Context manager for database sessions with automatic commit/rollback
        
        Usage:
            with db.session_scope() as session:
                session.add(user)
                # Auto-commit on success, auto-rollback on exception
        """
        session = self.get_session()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Database error: {e}")
            raise
        finally:
            session.close()
    
    def close(self):
        """Close all database connections"""
        self.ScopedSession.remove()
        self.engine.dispose()
        logger.info("Database connections closed")


# Dependency injection helper
def get_db_session(database: Database):
    """
    Dependency injection helper for FastAPI/Flask
    
    Usage:
        @app.route("/users")
        def get_users():
            with get_db_session(database) as session:
                users = session.query(User).all()
                return users
    """
    return database.session_scope()


# Singleton instance (set by application)
_db_instance = None


def init_database(database_url: str, **kwargs) -> Database:
    """
    Initialize global database instance
    
    Args:
        database_url: Database connection string
        **kwargs: Additional parameters
    
    Returns:
        Database: Initialized database instance
    """
    global _db_instance
    _db_instance = Database(database_url, **kwargs)
    return _db_instance


def get_database() -> Database:
    """
    Get global database instance
    
    Returns:
        Database: The database instance
    
    Raises:
        RuntimeError: If database not initialized
    """
    if _db_instance is None:
        raise RuntimeError("Database not initialized. Call init_database() first.")
    return _db_instance


# Transaction decorator
def transactional(func):
    """
    Decorator for transactional operations
    
    Usage:
        @transactional
        def create_user(session, name):
            user = User(name=name)
            session.add(user)
            return user
    """
    from functools import wraps
    
    @wraps(func)
    def wrapper(*args, **kwargs):
        db = get_database()
        with db.session_scope() as session:
            # Inject session as first argument if not present
            if 'session' not in kwargs:
                return func(session, *args, **kwargs)
            return func(*args, **kwargs)
    
    return wrapper


# Health check
def check_database_health() -> dict:
    """
    Check database connection health
    
    Returns:
        dict: Health status
    """
    try:
        db = get_database()
        with db.session_scope() as session:
            # Execute simple query
            session.execute("SELECT 1")
        
        return {
            "status": "healthy",
            "database": str(db.database_url).split('@')[-1],
            "pool_size": db.engine.pool.size() if hasattr(db.engine.pool, 'size') else None
        }
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e)
        }


if __name__ == "__main__":
    # Example usage
    import os
    
    # Initialize database
    db = init_database(
        database_url=os.getenv("DATABASE_URL", "sqlite:///test.db"),
        echo=True
    )
    
    # Create tables
    db.create_all_tables()
    
    # Test connection
    with db.session_scope() as session:
        result = session.execute("SELECT 1").scalar()
        print(f"Database test query result: {result}")
    
    # Health check
    health = check_database_health()
    print(f"Database health: {health}")
    
    # Cleanup
    db.close()