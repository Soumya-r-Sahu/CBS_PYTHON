"""
API Log Manager - Logs and monitors API integration activities
"""
from dataclasses import dataclass, asdict
from datetime import datetime
import json
import os
import threading
from typing import Dict, Any, Optional
import mysql.connector
from mysql.connector import pooling

# Constants for sensitive fields that should be redacted
SENSITIVE_FIELDS = ["password", "token", "key", "secret"]

@dataclass
class ApiLogEntry:
    timestamp: str
    endpoint: str
    request: dict
    response: dict
    status: str
    error: Optional[str] = None

class ApiLogger:
    def __init__(self, log_dir="integration/api_logs", max_file_size_mb=10):
        self.log_dir = log_dir
        self.max_file_size_mb = max_file_size_mb
        self.lock = threading.Lock()
        os.makedirs(log_dir, exist_ok=True)

    def _sanitize_data(self, data):
        """Sanitize sensitive data in requests/responses"""
        if isinstance(data, dict):
            sanitized = {}
            for key, value in data.items():
                if isinstance(value, (dict, list)):
                    sanitized[key] = self._sanitize_data(value)
                elif key.lower() in SENSITIVE_FIELDS:
                    sanitized[key] = "***REDACTED***"
                else:
                    sanitized[key] = value
            return sanitized
        elif isinstance(data, list):
            return [self._sanitize_data(item) if isinstance(item, (dict, list)) else item for item in data]
        return data

    def _rotate_logs_if_needed(self, log_file):
        """Rotate log file if it exceeds the maximum size"""
        if os.path.exists(log_file) and os.path.getsize(log_file) > self.max_file_size_mb * 1024 * 1024:
            base, ext = os.path.splitext(log_file)
            rotated_file = f"{base}_old{ext}"
            os.rename(log_file, rotated_file)

    def log_api_call(self, endpoint: str, request: Dict[str, Any], 
                     response: Dict[str, Any], status: str, error: Optional[str] = None) -> None:
        """Log an API interaction with a third-party service"""
        try:
            sanitized_request = self._sanitize_data(request)
            sanitized_response = self._sanitize_data(response)

            log_entry = ApiLogEntry(
                timestamp=datetime.utcnow().isoformat() + "Z",
                endpoint=endpoint,
                request=sanitized_request,
                response=sanitized_response,
                status=status,
                error=error
            )

            # Create log filename based on current date
            current_date = datetime.utcnow().strftime("%Y%m%d")
            log_file = f"{self.log_dir}/api_log_{current_date}.json"

            # Thread-safe write to log file
            with self.lock:
                with open(log_file, "a") as f:
                    f.write(json.dumps(asdict(log_entry)) + "\n")

        except Exception as e:
            print(f"Error logging API call: {e}")

class DatabaseApiLogger(ApiLogger):
    def __init__(self, log_dir="integration/api_logs", db_config=None, pool_size=5):
        super().__init__(log_dir)
        self.db_config = db_config or {
            'host': 'localhost',
            'database': 'core_banking_system',
            'user': 'root',
            'password': 'Admin.root@123',
            'port': 3307
        }
        self.pool_size = pool_size
        self.cnx_pool = mysql.connector.pooling.MySQLConnectionPool(
            pool_name="api_logger_pool",
            pool_size=self.pool_size,
            **self.db_config
        )
        self._verify_db_table()

    def _verify_db_table(self):
        """Ensure the API logs table exists"""
        try:
            cnx = self.cnx_pool.get_connection()
            cursor = cnx.cursor()
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS api_logs (
                    log_id BIGINT AUTO_INCREMENT PRIMARY KEY,
                    timestamp DATETIME NOT NULL,
                    endpoint VARCHAR(255) NOT NULL,
                    request_data JSON,
                    response_data JSON,
                    status VARCHAR(50) NOT NULL,
                    error TEXT
                ) ENGINE=InnoDB
                """
            )
            cnx.commit()
        finally:
            cursor.close()
            cnx.close()

    def log_api_call(self, endpoint: str, request: Dict[str, Any], 
                     response: Dict[str, Any], status: str, error: Optional[str] = None) -> None:
        """Log an API interaction to both file and database"""
        super().log_api_call(endpoint, request, response, status, error)
        try:
            cnx = self.cnx_pool.get_connection()
            cursor = cnx.cursor()
            cursor.execute(
                """
                INSERT INTO api_logs (timestamp, endpoint, request_data, response_data, status, error)
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (
                    datetime.utcnow(),
                    endpoint,
                    json.dumps(self._sanitize_data(request)),
                    json.dumps(self._sanitize_data(response)),
                    status,
                    error
                )
            )
            cnx.commit()
        finally:
            cursor.close()
            cnx.close()

if __name__ == "__main__":
    # Example usage
    logger = ApiLogger()
    logger.log_api_call(
        endpoint="/upi/transaction",
        request={"amount": 100, "to": "user123"},
        response={"result": "ok", "transaction_id": "tx_12345"},
        status="SUCCESS"
    )
    print("API call logged successfully")
