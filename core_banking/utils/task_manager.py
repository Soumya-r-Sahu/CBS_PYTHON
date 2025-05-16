"""
Task Manager

Manages background and scheduled tasks in the Core Banking System.
"""

import logging
import threading
import time
from datetime import datetime, timedelta
from typing import Dict, Any, Callable, List, Optional
import uuid

logger = logging.getLogger(__name__)

class TaskManager:
    """
    Handles background tasks, job scheduling, and task monitoring
    """
    
    def __init__(self):
        """Initialize task manager"""
        self.tasks = {}  # Task registry
        self.scheduled_tasks = {}  # Scheduled task registry
        self.running = True
        self._scheduler_thread = threading.Thread(target=self._scheduler_loop)
        self._scheduler_thread.daemon = True
        self._scheduler_thread.start()
    
    def submit_task(self, task_func: Callable, *args, **kwargs) -> str:
        """
        Submit a task to run in background
        
        Args:
            task_func: Function to execute
            *args: Arguments to pass to the function
            **kwargs: Keyword arguments to pass to the function
            
        Returns:
            Task ID
        """
        task_id = str(uuid.uuid4())
        
        # Create task object
        task = {
            'id': task_id,
            'function': task_func,
            'args': args,
            'kwargs': kwargs,
            'status': 'PENDING',
            'submitted_at': datetime.now(),
            'started_at': None,
            'completed_at': None,
            'result': None,
            'error': None
        }
        
        # Register task
        self.tasks[task_id] = task
        
        # Start task in a separate thread
        thread = threading.Thread(target=self._execute_task, args=(task_id,))
        thread.daemon = True
        thread.start()
        
        return task_id
    
    def _execute_task(self, task_id: str):
        """
        Execute a task and update its status
        
        Args:
            task_id: ID of the task to execute
        """
        if task_id not in self.tasks:
            logger.error(f"Task {task_id} not found")
            return
            
        task = self.tasks[task_id]
        task['status'] = 'RUNNING'
        task['started_at'] = datetime.now()
        
        try:
            # Execute the task
            result = task['function'](*task['args'], **task['kwargs'])
            
            # Update task with result
            task['status'] = 'COMPLETED'
            task['result'] = result
            task['completed_at'] = datetime.now()
            
        except Exception as e:
            # Update task with error
            task['status'] = 'FAILED'
            task['error'] = str(e)
            task['completed_at'] = datetime.now()
            logger.error(f"Task {task_id} failed: {str(e)}")
    
    def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """
        Get the status of a task
        
        Args:
            task_id: ID of the task
            
        Returns:
            Task status information
        """
        if task_id not in self.tasks:
            return {
                'success': False,
                'error': 'Task not found'
            }
            
        task = self.tasks[task_id]
        
        task_info = {
            'success': True,
            'id': task['id'],
            'status': task['status'],
            'submitted_at': task['submitted_at'].isoformat() if task['submitted_at'] else None,
            'started_at': task['started_at'].isoformat() if task['started_at'] else None,
            'completed_at': task['completed_at'].isoformat() if task['completed_at'] else None
        }
        
        # Include result or error if task is completed or failed
        if task['status'] == 'COMPLETED':
            task_info['result'] = task['result']
        elif task['status'] == 'FAILED':
            task_info['error'] = task['error']
            
        return task_info
    
    def schedule_task(self, task_func: Callable, 
                    schedule_time: datetime = None,
                    delay: int = None,
                    recurrent: bool = False,
                    interval: int = None,
                    *args, **kwargs) -> str:
        """
        Schedule a task to run at a specific time or after a delay
        
        Args:
            task_func: Function to execute
            schedule_time: Specific time to run the task
            delay: Delay in seconds before running the task
            recurrent: Whether the task should repeat
            interval: Interval in seconds for recurrent tasks
            *args: Arguments to pass to the function
            **kwargs: Keyword arguments to pass to the function
            
        Returns:
            Scheduled task ID
        """
        # Generate ID
        task_id = str(uuid.uuid4())
        
        # Calculate execution time
        if schedule_time:
            next_run = schedule_time
        elif delay:
            next_run = datetime.now() + timedelta(seconds=delay)
        else:
            next_run = datetime.now()
            
        # Create scheduled task
        scheduled_task = {
            'id': task_id,
            'function': task_func,
            'args': args,
            'kwargs': kwargs,
            'next_run': next_run,
            'recurrent': recurrent,
            'interval': interval,
            'status': 'SCHEDULED',
            'created_at': datetime.now(),
            'last_run': None
        }
        
        # Register scheduled task
        self.scheduled_tasks[task_id] = scheduled_task
        
        return task_id
    
    def _scheduler_loop(self):
        """
        Background thread that checks for scheduled tasks
        """
        while self.running:
            try:
                now = datetime.now()
                
                # Check for tasks to run
                for task_id, task in list(self.scheduled_tasks.items()):
                    if task['next_run'] <= now:
                        # Submit task for execution
                        execution_id = self.submit_task(task['function'], *task['args'], **task['kwargs'])
                        
                        # Update last run time
                        task['last_run'] = now
                        
                        # If recurrent, schedule next run
                        if task['recurrent'] and task['interval']:
                            task['next_run'] = now + timedelta(seconds=task['interval'])
                        else:
                            # One-time task, remove from schedule
                            del self.scheduled_tasks[task_id]
            except Exception as e:
                logger.error(f"Error in scheduler loop: {str(e)}")
                
            # Sleep for a short time before checking again
            time.sleep(1)
    
    def cancel_scheduled_task(self, task_id: str) -> bool:
        """
        Cancel a scheduled task
        
        Args:
            task_id: ID of the scheduled task
            
        Returns:
            Boolean indicating success
        """
        if task_id in self.scheduled_tasks:
            del self.scheduled_tasks[task_id]
            return True
        return False
    
    def get_scheduled_tasks(self) -> List[Dict[str, Any]]:
        """
        Get a list of all scheduled tasks
        
        Returns:
            List of scheduled tasks
        """
        tasks = []
        for task_id, task in self.scheduled_tasks.items():
            task_info = {
                'id': task_id,
                'next_run': task['next_run'].isoformat() if task['next_run'] else None,
                'recurrent': task['recurrent'],
                'interval': task['interval'],
                'status': task['status'],
                'created_at': task['created_at'].isoformat() if task['created_at'] else None,
                'last_run': task['last_run'].isoformat() if task['last_run'] else None
            }
            tasks.append(task_info)
            
        return tasks
    
    def shutdown(self):
        """Shutdown the task manager"""
        self.running = False
        if self._scheduler_thread.is_alive():
            self._scheduler_thread.join(2)  # Wait up to 2 seconds

# Create singleton instance
task_manager = TaskManager()
