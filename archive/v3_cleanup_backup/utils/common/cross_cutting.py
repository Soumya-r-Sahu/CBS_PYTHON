"""
Cross-Cutting Concerns Module

This module provides functionality for cross-cutting concerns like
error handling, logging, and security that span multiple domains.
"""
import logging
import os
from datetime import datetime
from functools import wraps
from typing import Callable, Dict, Any, Type, List, Optional

# Configure logging
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
LOG_LEVEL = os.environ.get('CBS_LOG_LEVEL', 'INFO').upper()
LOG_FILE = os.environ.get('CBS_LOG_FILE', 'cbs_system.log')

# Create logger
logger = logging.getLogger('cbs_system')
logger.setLevel(getattr(logging, LOG_LEVEL))

# Add handlers if none exist
if not logger.handlers:
    # Create console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(getattr(logging, LOG_LEVEL))
    
    # Create file handler
    file_handler = logging.FileHandler(LOG_FILE)
    file_handler.setLevel(getattr(logging, LOG_LEVEL))
    
    # Create formatter
    formatter = logging.Formatter(LOG_FORMAT)
    
    # Add formatter to handlers
    console_handler.setFormatter(formatter)
    file_handler.setFormatter(formatter)
    
    # Add handlers to logger
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

def log_execution_time(func):
    """Decorator to log execution time of functions."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        """Wrapper function."""
        start_time = datetime.now()
        logger.debug(f"Starting {func.__name__}...")
        result = func(*args, **kwargs)
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        logger.debug(f"Completed {func.__name__} in {duration:.2f} seconds")
        return result
    return wrapper

def handle_exceptions(logger_instance=None, retry_count=0, retry_delay=1,
                     allowed_exceptions=None, reraise=True):
    """
    Decorator to handle exceptions with optional retry logic.
    
    Args:
        logger_instance: Logger to use (defaults to module logger)
        retry_count: Number of retries on exception
        retry_delay: Delay between retries in seconds
        allowed_exceptions: List of exception types to handle
        reraise: Whether to reraise the exception after handling
    
    Returns:
        Decorator function
    """
    log = logger_instance or logger
    
    def decorator(func):
        """Decorator function."""
        @wraps(func)
        def wrapper(*args, **kwargs):
            """Wrapper function."""
            last_exception = None
            allowed = allowed_exceptions or [Exception]
            
            for attempt in range(retry_count + 1):
                try:
                    return func(*args, **kwargs)
                except tuple(allowed) as exc:
                    last_exception = exc
                    log.warning(
                        f"Exception in {func.__name__} (attempt {attempt+1}/{retry_count+1}): {str(exc)}"
                    )
                    if attempt < retry_count:
                        import time
                        time.sleep(retry_delay)
                except Exception as exc:
                    log.error(f"Unhandled exception in {func.__name__}: {str(exc)}")
                    raise
            
            if reraise and last_exception:
                log.error(f"All {retry_count+1} attempts failed for {func.__name__}")
                raise last_exception
        return wrapper
    return decorator

def monitor_resource_usage(threshold_cpu=80, threshold_memory=80):
    """
    Decorator to monitor CPU and memory usage during function execution.
    
    Args:
        threshold_cpu: CPU usage threshold percentage
        threshold_memory: Memory usage threshold percentage
    
    Returns:
        Decorator function
    """
    def decorator(func):
        """Decorator function."""
        @wraps(func)
        def wrapper(*args, **kwargs):
            """Wrapper function."""
            try:
                import psutil
                process = psutil.Process(os.getpid())
                
                # Get initial CPU and memory usage
                initial_cpu = process.cpu_percent()
                initial_memory = process.memory_percent()
                
                # Execute function
                result = func(*args, **kwargs)
                
                # Get final CPU and memory usage
                final_cpu = process.cpu_percent()
                final_memory = process.memory_percent()
                
                # Log resource usage
                logger.info(f"Resource usage for {func.__name__}: CPU: {final_cpu:.1f}%, Memory: {final_memory:.1f}%")
                
                # Check thresholds
                if final_cpu > threshold_cpu:
                    logger.warning(f"High CPU usage detected in {func.__name__}: {final_cpu:.1f}%")
                if final_memory > threshold_memory:
                    logger.warning(f"High memory usage detected in {func.__name__}: {final_memory:.1f}%")
                
                return result
            except ImportError:
                logger.warning("psutil not installed, resource monitoring disabled")
                return func(*args, **kwargs)
        return wrapper
    return decorator

def trace_function_calls(trace_args=False, trace_result=False):
    """
    Decorator to trace function calls for debugging.
    
    Args:
        trace_args: Whether to log function arguments
        trace_result: Whether to log function return value
    
    Returns:
        Decorator function
    """
    def decorator(func):
        """Decorator function."""
        @wraps(func)
        def wrapper(*args, **kwargs):
            """Wrapper function."""
            func_name = func.__name__
            module_name = func.__module__
            
            # Log entry
            entry_msg = f"TRACE: Entering {module_name}.{func_name}()"
            if trace_args and (args or kwargs):
                args_repr = [repr(a) for a in args]
                kwargs_repr = [f"{k}={repr(v)}" for k, v in kwargs.items()]
                all_args = args_repr + kwargs_repr
                entry_msg += f" with args: {', '.join(all_args)}"
            logger.debug(entry_msg)
            
            # Execute function
            result = func(*args, **kwargs)
            
            # Log exit
            exit_msg = f"TRACE: Exiting {module_name}.{func_name}()"
            if trace_result:
                exit_msg += f" with result: {repr(result)}"
            logger.debug(exit_msg)
            
            return result
        return wrapper
    return decorator


# Alias for backward compatibility
exception_handler = handle_exceptions
