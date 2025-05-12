"""
Database migration utilities for the Core Banking System.

This module provides functions to apply and rollback database migrations.
"""
import os

def list_migrations(migrations_dir):
    """List all migration scripts in the migrations directory."""
    return [f for f in os.listdir(migrations_dir) if f.endswith('.sql')]

def apply_migration(migration_file, connection):
    """Apply a single migration script to the database."""
    with open(migration_file, 'r') as f:
        sql = f.read()
    cursor = connection.cursor()
    for statement in sql.split(';'):
        if statement.strip():
            cursor.execute(statement)
    connection.commit()
    cursor.close()

def rollback_migration(migration_file, connection):
    """Rollback a migration (if down section is present)."""
    with open(migration_file, 'r') as f:
        sql = f.read()
    if '-- Down' in sql:
        down_sql = sql.split('-- Down')[1]
        cursor = connection.cursor()
        for statement in down_sql.split(';'):
            if statement.strip():
                cursor.execute(statement)
        connection.commit()
        cursor.close()
    else:
        print('No rollback section found in migration.')
