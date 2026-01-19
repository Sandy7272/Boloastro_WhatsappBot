# worker.py
from redis import Redis
from rq import Worker, Queue, Connection
from config import Config
from database import init_db

listen = ['default']

if __name__ == '__main__':
    # Initialize DB connection for the worker
    init_db()
    
    conn = Redis.from_url(Config.REDIS_URL)
    
    with Connection(conn):
        worker = Worker(list(map(Queue, listen)))
        worker.work()