import psycopg2
import os

def get_connection():
    return psycopg2.connect(
        host="localhost",
        database="boloastro_db",
        user="postgres",
        password="Sandesh@7272"
    )
