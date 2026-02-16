import sqlite3
import os
import logging

logger = logging.getLogger(__name__)


def get_db_path():
    return os.path.join(os.path.dirname(os.path.dirname(__file__)), 
                        os.getenv('DATABASE_PATH', 'medsync.db'))


def get_db():
    """Get a database connection with foreign keys enabled."""
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    """Initialize database from schema file."""
    db_path = get_db_path()
    schema_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'backend', 'schema.sql')
    
    if not os.path.exists(schema_path):
        schema_path = os.path.join(os.path.dirname(__file__), '..', 'schema.sql')
    
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")
    
    with open(schema_path, 'r') as f:
        conn.executescript(f.read())
    
    conn.commit()
    conn.close()
    logger.info(f"Database initialized at {db_path}")


def query_db(query, args=(), one=False):
    """Execute a query and return results."""
    conn = get_db()
    try:
        cur = conn.execute(query, args)
        rv = cur.fetchall()
        conn.commit()
        return (rv[0] if rv else None) if one else rv
    finally:
        conn.close()


def execute_db(query, args=()):
    """Execute an insert/update/delete and return lastrowid."""
    conn = get_db()
    try:
        cur = conn.execute(query, args)
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()
