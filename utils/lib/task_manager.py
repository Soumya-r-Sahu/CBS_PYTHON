"""
Task Manager

Provides functionality for asynchronous task execution in the Core Banking System.
"""

import logging
import threading
import queue
import time
from typing import Callable, Any, Dict, List, Optional
import importlib

logger = logging.getLogger(__name__)

class TaskManager:
    """
    Manager for asynchronous task execution
    
    Features:
    - Submit tasks for background execution
    - Monitor task execution
    - Task prioritization
    - Task status tracking
    """
    
    def __init__(self, max_workers: int = 5):
        """
        Initialize task manager
        
        Args:
            max_workers: Maximum number of worker threads
        """
        self.task_queue = queue.PriorityQueue()
        self.results = {}
        self.workers = []
        self.max_workers = max_workers
        self.next_task_id = 1
        self.running = False
        self.lock = threading.Lock()
        
        logger.info("Task manager initialized with %d workers", max_workers)
    
    def start(self):
        """Start the task manager worker threads"""
        if self.running:
            return
            
        self.running = True
        
        for i in range(self.max_workers):
            worker = threading.Thread(target=self._worker_loop, name=f"TaskWorker-{i+1}")
            worker.daemon = True
            worker.start()
            self.workers.append(worker)
            
        logger.info("Task manager started")
    
    def stop(self):
        """Stop the task manager"""
        self.running = False
        
        for worker in self.workers:
            worker.join(timeout=1.0)
            
        self.workers = []
        logger.info("Task manager stopped")
    
    def submit_task(self, task_path: str, *args, **kwargs) -> str:
        """
        Submit a task for execution
        
        Args:
            task_path: Import path to the function to execute
            *args: Positional arguments to pass to the function
            **kwargs: Keyword arguments to pass to the function
            
        Returns:
            Task ID
        """
        with self.lock:
            task_id = f"task_{self.next_task_id}"
            self.next_task_id += 1
            
        # Default priority is 1 (lower number = higher priority)
        priority = kwargs.pop('_priority', 1)
        
        # Create task item
        task_item = {
            'id': task_id,
            'path': task_path,
            'args': args,
            'kwargs': kwargs,
            'submitted_at': time.time()
        }
        
        # Store result placeholder
        self.results[task_id] = {
            'status': 'PENDING',
            'result': None,
            'error': None,
            'completed_at': None
        }
        
        # Add to queue
        self.task_queue.put((priority, task_item))
        
        logger.debug("Task %s submitted: %s", task_id, task_path)
        
        # Auto-start if not running
        if not self.running:
            self.start()
            
        return task_id
    
    def get_result(self, task_id: str, wait: bool = False, timeout: Optional[float] = None) -> Dict[str, Any]:
        """
        Get task result
        
        Args:
            task_id: Task ID
            wait: Whether to wait for the task to complete
            timeout: Maximum time to wait in seconds
            
        Returns:
            Task result dictionary
        """
        if task_id not in self.results:
            return {
                'status': 'UNKNOWN',
                'error': 'Task ID not found'
            }
            
        result = self.results[task_id]
        
        # If not waiting or already completed, return current status
        if not wait or result['status'] in ('COMPLETED', 'FAILED'):
            return result
            
        # Wait for completion
        start_time = time.time()
        while result['status'] == 'PENDING':
            time.sleep(0.1)
            
            # Check timeout
            if timeout and time.time() - start_time > timeout:
                return {
                    'status': 'TIMEOUT',
                    'error': f'Task did not complete within {timeout} seconds'
                }
                
        return result
    
    def _worker_loop(self):
        """Worker thread loop"""
        while self.running:
            try:
                # Get next task
                try:
                    _, task_item = self.task_queue.get(timeout=1.0)
                except queue.Empty:
                    continue
                    
                task_id = task_item['id']
                task_path = task_item['path']
                args = task_item['args']
                kwargs = task_item['kwargs']
                
                logger.debug("Processing task %s: %s", task_id, task_path)
                
                try:
                    # Split module and function
                    module_path, function_name = task_path.rsplit('.', 1)
                    
                    # Import module
                    module = importlib.import_module(module_path)
                    
                    # Get function
                    func = getattr(module, function_name)
                    
                    # Execute function
                    result = func(*args, **kwargs)
                    
                    # Store result
                    self.results[task_id] = {
                        'status': 'COMPLETED',
                        'result': result,
                        'error': None,
                        'completed_at': time.time()
                    }
                    
                    logger.debug("Task %s completed successfully", task_id)
                    
                except Exception as e:
                    logger.error("Task %s failed: %s", task_id, str(e), exc_info=True)
                    
                    # Store error
                    self.results[task_id] = {
                        'status': 'FAILED',
                        'result': None,
                        'error': str(e),
                        'completed_at': time.time()
                    }
                    
                finally:
                    self.task_queue.task_done()
                    
            except Exception as e:
                logger.error("Worker thread error: %s", str(e), exc_info=True)
                time.sleep(1.0)  # Prevent tight loop on repeated errors
    
    def get_pending_tasks(self) -> List[str]:
        """Get list of pending task IDs"""
        return [
            task_id for task_id, result in self.results.items() 
            if result['status'] == 'PENDING'
        ]
    
    def get_failed_tasks(self) -> List[str]:
        """Get list of failed task IDs"""
        return [
            task_id for task_id, result in self.results.items() 
            if result['status'] == 'FAILED'
        ]
    
    def cancel_task(self, task_id: str) -> bool:
        """
        Cancel a pending task
        
        Note: Can only cancel tasks that haven't started processing
        
        Args:
            task_id: Task ID to cancel
            
        Returns:
            True if task was canceled, False otherwise
        """
        # Tasks currently being processed can't be canceled
        # This would require a more complex implementation
        if task_id not in self.results or self.results[task_id]['status'] != 'PENDING':
            return False
            
        # Mark as canceled
        self.results[task_id] = {
            'status': 'CANCELED',
            'result': None,
            'error': 'Task canceled',
            'completed_at': time.time()
        }
        
        return True
        
    def clear_completed_tasks(self, max_age: Optional[float] = None):
        """
        Clear completed task results to free memory
        
        Args:
            max_age: Clear only results older than this many seconds
        """
        current_time = time.time()
        
        to_clear = []
        for task_id, result in self.results.items():
            if result['status'] in ('COMPLETED', 'FAILED', 'CANCELED'):
                if result.get('completed_at') and (
                    not max_age or current_time - result['completed_at'] > max_age
                ):
                    to_clear.append(task_id)
                    
        for task_id in to_clear:
            del self.results[task_id]
            
        logger.debug("Cleared %d completed task results", len(to_clear))
        

# Singleton instance
task_manager = TaskManager()

# Auto-start the task manager when imported
task_manager.start()
