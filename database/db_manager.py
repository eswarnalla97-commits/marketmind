import sqlite3
import os
import pandas as pd
from config import config

def get_db_connection():
    """Returns a SQLite connection with row factory configured."""
    os.makedirs(os.path.dirname(config.DATABASE_PATH), exist_ok=True)
    conn = sqlite3.connect(config.DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def init_db():
    """Initializes the database using schema.sql."""
    schema_path = os.path.join(os.path.dirname(__file__), 'schema.sql')
    with open(schema_path, 'r', encoding='utf-8') as f:
        schema_sql = f.read()
    
    conn = get_db_connection()
    try:
        conn.executescript(schema_sql)
        conn.commit()
    finally:
        conn.close()

def query_df(query, params=None):
    """Executes a SQL query and returns the result as a pandas DataFrame."""
    conn = get_db_connection()
    try:
        if params:
            df = pd.read_sql_query(query, conn, params=params)
        else:
            df = pd.read_sql_query(query, conn)
        return df
    finally:
        conn.close()

def query_rows(query, params=None):
    """Executes a SQL query and returns list of dictionaries."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        rows = [dict(row) for row in cursor.fetchall()]
        return rows
    finally:
        conn.close()

def query_scalar(query, params=None):
    """Executes a query returning a single scalar value."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        row = cursor.fetchone()
        return row[0] if row else None
    finally:
        conn.close()

def execute_commit(query, params=None):
    """Executes an INSERT, UPDATE, or DELETE query and commits."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()

def get_warehouse_stats():
    """Returns row counts and health metrics for the warehouse."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        stats = {}
        for table in ['FactSales', 'DimCustomer', 'DimProduct', 'DimDate', 'DimOrder', 'StagingTransactions', 'ETLHistory', 'FeedbackSubmissions', 'Users', 'ActivityLogs']:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                stats[table] = cursor.fetchone()[0]
            except Exception:
                stats[table] = 0
        return stats
    finally:
        conn.close()
