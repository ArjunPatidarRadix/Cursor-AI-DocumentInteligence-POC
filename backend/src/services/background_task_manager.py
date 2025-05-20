import asyncio
from typing import Dict, Any, Callable, Awaitable, Coroutine
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BackgroundTaskManager:
    def __init__(self):
        self._tasks: Dict[str, asyncio.Task] = {}
        self._task_status: Dict[str, Dict[str, Any]] = {}

    def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """Get the status of a specific task."""
        return self._task_status.get(task_id, {})

    async def create_task(
        self,
        task_id: str,
        coro: Coroutine,
        on_complete: Callable[[str, Any], Awaitable] = None,
        on_error: Callable[[str, Exception], Awaitable] = None
    ) -> None:
        """Create and start a new background task."""
        
        if task_id in self._tasks:
            logger.warning(f"Task {task_id} is already running")
            return

        async def wrapped_task():
            try:
                self._task_status[task_id] = {
                    "status": "running",
                    "start_time": datetime.utcnow(),
                    "error": None
                }
                
                # Execute the actual task
                result = await coro
                
                # Update status on completion
                self._task_status[task_id]["status"] = "completed"
                self._task_status[task_id]["completion_time"] = datetime.utcnow()
                
                # Call completion callback if provided
                if on_complete:
                    try:
                        await on_complete(task_id, result)
                    except Exception as callback_error:
                        logger.error(f"Error in completion callback for task {task_id}: {str(callback_error)}")
                    
            except Exception as e:
                logger.error(f"Task {task_id} failed: {str(e)}")
                self._task_status[task_id] = {
                    "status": "failed",
                    "error": str(e),
                    "completion_time": datetime.utcnow()
                }
                
                # Call error callback if provided
                if on_error:
                    try:
                        await on_error(task_id, e)
                    except Exception as callback_error:
                        logger.error(f"Error in error callback for task {task_id}: {str(callback_error)}")
            finally:
                # Clean up task references
                if task_id in self._tasks:
                    del self._tasks[task_id]
                # Keep status for a while but eventually clean it up
                asyncio.create_task(self._cleanup_status(task_id))

        # Create and store the task
        task = asyncio.create_task(wrapped_task())
        self._tasks[task_id] = task

    async def _cleanup_status(self, task_id: str, delay: int = 3600):
        """Clean up task status after a delay (default 1 hour)."""
        await asyncio.sleep(delay)
        if task_id in self._task_status:
            del self._task_status[task_id]

    def is_task_running(self, task_id: str) -> bool:
        """Check if a task is currently running."""
        return task_id in self._tasks

# Create singleton instance
background_task_manager = BackgroundTaskManager() 