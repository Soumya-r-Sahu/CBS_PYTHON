"""
Core Banking System Logging Module

This module provides a centralized, thread-safe logging configuration for all
components of the Core Banking System. It sets up properly configured loggers
with appropriate handlers based on the environment.

Features:
- Asynchronous logging using queue handlers for better performance
- Automatic log rotation with compression of old logs
- Environment-specific log levels and formatting
- Console and file-based logging
- Error tracking and alerting options

Usage:
    from utils.logging import get_logger
    
    # Get a logger for your module
    logger = get_logger(__name__)
    
    # Use standard logging levels
    logger.debug("Detailed debugging information")
    logger.info("Normal operation information")
    logger.warning("Warning message")
    logger.error("Error message")
    logger.critical("Critical error message")
"""

import os
import sys
import queue
import logging
import threading
import time
from pathlib import Path
from logging.handlers import TimedRotatingFileHandler, QueueHandler, QueueListener

# Add parent directory to path if needed for importing from config
try:
    from utils.lib.packages import fix_path
    fix_path()  # Ensures the project root is in sys.path
except ImportError:
    # Fallback if the import manager is not available
    parent_dir = str(Path(__file__).parent.parent)
    if parent_dir not in sys.path:
        sys.path.insert(0, parent_dir)

try:
    from utils.config.environment import is_production, is_development, is_test, is_debug_enabled
except ImportError:
    # Fallback environment detection if module import fails
    env_str = os.environ.get("CBS_ENVIRONMENT", "development").lower()
    def is_production(): return env_str == "production"
    def is_development(): return env_str == "development"
    def is_test(): return env_str == "test"
    def is_debug_enabled(): return os.environ.get("CBS_DEBUG", "true").lower() in ("true", "1", "yes") and not is_production()

# Determine log level from environment
log_level_str = os.environ.get("CBS_LOG_LEVEL", "INFO" if is_production() else "DEBUG")
log_level = getattr(logging, log_level_str.upper(), logging.INFO)

# Get buffer size from environment or config 
buffer_size = int(os.environ.get("CBS_LOG_BUFFER_SIZE", 1000))
buffer_flush_interval = float(os.environ.get("CBS_LOG_FLUSH_INTERVAL", 0.5))  # in seconds

# Initialize buffer and listener
log_queue = queue.Queue(maxsize=buffer_size)
queue_handler = None
queue_listener = None

def setup_logging():
    """Setup the logging configuration"""
    global queue_handler, queue_listener
    
    # Configure handlers based on environment
    handlers = []
    formatter = logging.Formatter('%(asctime)s - [%(levelname)s] - %(name)s - %(message)s')

    # Always log to file with different paths per environment
    log_file = "app_prod.log" if is_production() else "app_dev.log" if is_development() else "app_test.log"
    log_dir = Path(__file__).parent.parent / "logs"
    
    # Create different log directories per environment
    env_name = "production" if is_production() else "development" if is_development() else "test"
    env_log_dir = log_dir / env_name
    os.makedirs(env_log_dir, exist_ok=True)
    
    # Set up a rotating file handler
    file_handler = TimedRotatingFileHandler(
        env_log_dir / log_file,
        when='midnight',
        interval=1,
        backupCount=7 if is_production() else 3
    )
    file_handler.setFormatter(formatter)
    handlers.append(file_handler)

    # Console handler based on environment
    if not is_production() or is_debug_enabled():
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        handlers.append(console_handler)
        
    # Create queue listener
    queue_listener = QueueListener(log_queue, *handlers, respect_handler_level=True)
    queue_handler = QueueHandler(log_queue)
    
    # Configure the root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    root_logger.addHandler(queue_handler)
    
    # Start the queue listener in a separate thread
    queue_listener.start()
    
    return root_logger

# Initialize logging
root_logger = setup_logging()

# Performance optimization for high-volume logging
class BufferedLogger:
    """
    A high-performance logger for high-volume operations.
    Buffers log messages and flushes them periodically or when the buffer is full.
    """
    
    def __init__(self, name, buffer_size=100):
        self.logger = logging.getLogger(name)
        self.buffer = []
        self.buffer_size = buffer_size
        self.lock = threading.RLock()
        self._setup_flusher()
        
    def _setup_flusher(self):
        """Start a background thread to periodically flush logs"""
        self.stop_event = threading.Event()
        self.flush_thread = threading.Thread(target=self._periodic_flush, daemon=True)
        self.flush_thread.start()
        
    def _periodic_flush(self):
        """Periodically flush logs"""
        while not self.stop_event.is_set():
            time.sleep(buffer_flush_interval)
            self.flush()
            
    def stop(self):
        """Stop the background flusher thread"""
        self.stop_event.set()
        self.flush()  # Final flush
        
    def flush(self):
        """Flush buffered logs"""
        with self.lock:
            if self.buffer:
                for level, msg, args, kwargs in self.buffer:
                    if level == logging.INFO:
                        self.logger.info(msg, *args, **kwargs)
                    elif level == logging.DEBUG:
                        self.logger.debug(msg, *args, **kwargs)
                    elif level == logging.WARNING:
                        self.logger.warning(msg, *args, **kwargs)
                    elif level == logging.ERROR:
                        self.logger.error(msg, *args, **kwargs)
                    elif level == logging.CRITICAL:
                        self.logger.critical(msg, *args, **kwargs)
                self.buffer = []
                
    def _log(self, level, msg, *args, **kwargs):
        """Add a log message to the buffer"""
        # Direct logging for critical and error messages
        if level >= logging.ERROR or self.logger.level <= logging.DEBUG:
            if level == logging.INFO:
                self.logger.info(msg, *args, **kwargs)
            elif level == logging.DEBUG:
                self.logger.debug(msg, *args, **kwargs)
            elif level == logging.WARNING:
                self.logger.warning(msg, *args, **kwargs)
            elif level == logging.ERROR:
                self.logger.error(msg, *args, **kwargs)
            elif level == logging.CRITICAL:
                self.logger.critical(msg, *args, **kwargs)
        else:
            # Buffer other messages
            with self.lock:
                self.buffer.append((level, msg, args, kwargs))
                if len(self.buffer) >= self.buffer_size:
                    self.flush()
                    
    def debug(self, msg, *args, **kwargs):
        """Log a debug message"""
        self._log(logging.DEBUG, msg, *args, **kwargs)
        
    def info(self, msg, *args, **kwargs):
        """Log an info message"""
        self._log(logging.INFO, msg, *args, **kwargs)
        
    def warning(self, msg, *args, **kwargs):
        """Log a warning message"""
        self._log(logging.WARNING, msg, *args, **kwargs)
        
    def error(self, msg, *args, **kwargs):
        """Log an error message"""
        self._log(logging.ERROR, msg, *args, **kwargs)
        
    def critical(self, msg, *args, **kwargs):
        """Log a critical message"""
        self._log(logging.CRITICAL, msg, *args, **kwargs)
        
    def exception(self, msg, *args, **kwargs):
        """Log an exception"""
        self._log(logging.ERROR, msg, *args, exc_info=True, **kwargs)

# Export standard logging functions
def log_info(message):
    logging.info(message)

def log_warning(message):
    logging.warning(message)

def log_error(message):
    logging.error(message)

def log_debug(message):
    logging.debug(message)

def get_logger(name: str) -> logging.Logger:
    """Get a standard logger with the specified name"""
    return logging.getLogger(name)

def get_buffered_logger(name: str, buffer_size: int = None) -> BufferedLogger:
    """Get a buffered logger optimized for high-volume logging"""
    return BufferedLogger(name, buffer_size or buffer_size)

def shutdown():
    """Properly shut down logging"""
    if queue_listener:
        queue_listener.stop()
    logging.shutdown()

# Make sure logging is shut down properly on exit
import atexit
atexit.register(shutdown)

# Example usage in high-volume operations:
# high_volume_logger = get_buffered_logger("high_volume_operations")
# for i in range(10000):
#     high_volume_logger.info(f"Processing item {i}")
# high_volume_logger.flush()  # Ensure any remaining logs are written
