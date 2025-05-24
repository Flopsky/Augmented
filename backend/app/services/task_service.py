from sqlalchemy.orm import Session
from app.models.task import Task
from app.models.schemas import TaskCreate, TaskUpdate, TaskResponse
from typing import List, Optional
import logging
from fuzzywuzzy import fuzz

logger = logging.getLogger(__name__)

class TaskService:
    def __init__(self, db: Session):
        self.db = db
    
    def create_task(self, task_data: TaskCreate) -> TaskResponse:
        """Create a new task"""
        try:
            db_task = Task(
                description=task_data.description,
                priority=task_data.priority,
                category=task_data.category.value if task_data.category else "personal",
                remind_at=task_data.remind_at,
                recurring=task_data.recurring
            )
            
            self.db.add(db_task)
            self.db.commit()
            self.db.refresh(db_task)
            
            logger.info(f"Created task: {db_task.description}")
            return TaskResponse.from_orm(db_task)
            
        except Exception as e:
            logger.error(f"Error creating task: {e}")
            self.db.rollback()
            raise
    
    def get_tasks(self, include_completed: bool = False) -> List[TaskResponse]:
        """Get all tasks, optionally including completed ones"""
        try:
            query = self.db.query(Task)
            if not include_completed:
                query = query.filter(Task.completed == False)
            
            tasks = query.order_by(Task.priority.desc(), Task.created_at.desc()).all()
            return [TaskResponse.from_orm(task) for task in tasks]
            
        except Exception as e:
            logger.error(f"Error getting tasks: {e}")
            return []
    
    def get_task(self, task_id: int) -> Optional[TaskResponse]:
        """Get a specific task by ID"""
        try:
            task = self.db.query(Task).filter(Task.id == task_id).first()
            return TaskResponse.from_orm(task) if task else None
        except Exception as e:
            logger.error(f"Error getting task {task_id}: {e}")
            return None
    
    def update_task(self, task_id: int, task_data: TaskUpdate) -> Optional[TaskResponse]:
        """Update an existing task"""
        try:
            task = self.db.query(Task).filter(Task.id == task_id).first()
            if not task:
                return None
            
            update_data = task_data.dict(exclude_unset=True)
            for field, value in update_data.items():
                if field == "category" and value:
                    setattr(task, field, value.value)
                else:
                    setattr(task, field, value)
            
            self.db.commit()
            self.db.refresh(task)
            
            logger.info(f"Updated task {task_id}: {task.description}")
            return TaskResponse.from_orm(task)
            
        except Exception as e:
            logger.error(f"Error updating task {task_id}: {e}")
            self.db.rollback()
            raise
    
    def delete_task(self, task_id: int) -> bool:
        """Delete a task"""
        try:
            task = self.db.query(Task).filter(Task.id == task_id).first()
            if not task:
                return False
            
            self.db.delete(task)
            self.db.commit()
            
            logger.info(f"Deleted task {task_id}: {task.description}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting task {task_id}: {e}")
            self.db.rollback()
            return False
    
    def complete_task(self, task_id: int) -> Optional[TaskResponse]:
        """Mark a task as completed"""
        return self.update_task(task_id, TaskUpdate(completed=True))
    
    def find_task_by_description(self, description: str, threshold: int = 60) -> Optional[Task]:
        """Find a task using fuzzy string matching"""
        try:
            active_tasks = self.db.query(Task).filter(Task.completed == False).all()
            
            best_match = None
            best_score = 0
            
            for task in active_tasks:
                # Calculate similarity score
                score = fuzz.partial_ratio(description.lower(), task.description.lower())
                if score > best_score and score >= threshold:
                    best_score = score
                    best_match = task
            
            if best_match:
                logger.info(f"Found task match: '{description}' -> '{best_match.description}' (score: {best_score})")
            
            return best_match
            
        except Exception as e:
            logger.error(f"Error finding task by description: {e}")
            return None
    
    def clear_completed_tasks(self) -> int:
        """Remove all completed tasks"""
        try:
            completed_tasks = self.db.query(Task).filter(Task.completed == True).all()
            count = len(completed_tasks)
            
            for task in completed_tasks:
                self.db.delete(task)
            
            self.db.commit()
            logger.info(f"Cleared {count} completed tasks")
            return count
            
        except Exception as e:
            logger.error(f"Error clearing completed tasks: {e}")
            self.db.rollback()
            return 0
    
    def get_tasks_dict(self) -> List[dict]:
        """Get tasks as dictionary for Claude context"""
        tasks = self.get_tasks(include_completed=False)
        return [
            {
                "id": task.id,
                "description": task.description,
                "priority": task.priority,
                "category": task.category
            }
            for task in tasks
        ]