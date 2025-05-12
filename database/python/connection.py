import mysql.connector
from mysql.connector import Error, pooling
from utils.config import DATABASE_CONFIG

class DatabaseConnection:
    def __init__(self):
        self.pool = mysql.connector.pooling.MySQLConnectionPool(
            pool_name="db_pool",
            pool_size=5,
            **DATABASE_CONFIG
        )

    def get_connection(self):
        """Get a connection from the pool"""
        try:
            return self.pool.get_connection()
        except Error as e:
            print(f"Error getting connection from pool: {e}")
            return None

    def close_connection(self, connection):
        """Close a specific connection"""
        if connection and connection.is_connected():
            connection.close()
