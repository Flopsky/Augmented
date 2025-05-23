from pydantic import BaseModel, Field
from typing import Optional, List, Literal
from enum import Enum
from datetime import datetime

class ActionType(str, Enum):
    ADD_TASK = "add_task"
    COMPLETE_TASK = "complete_task"
    LIST_TASKS = "list_tasks"
    MODIFY_TASK = "modify_task"
    CLEAR_COMPLETED = "clear_completed"
    UPDATE_REMINDER = "update_reminder"
    UNCLEAR = "unclear"

class TaskCategory(str, Enum):
    SHOPPING = "shopping"
    WORK = "work"
    PERSONAL = "personal"
    URGENT = "urgent"

class TaskBase(BaseModel):
    description: str
    priority: Optional[int] = Field(default=3, ge=1, le=5)
    category: Optional[TaskCategory] = TaskCategory.PERSONAL
    remind_at: Optional[datetime] = None
    recurring: Optional[bool] = False

class TaskCreate(TaskBase):
    pass

class TaskUpdate(BaseModel):
    description: Optional[str] = None
    completed: Optional[bool] = None
    priority: Optional[int] = Field(None, ge=1, le=5)
    category: Optional[TaskCategory] = None
    remind_at: Optional[datetime] = None
    recurring: Optional[bool] = None

class TaskResponse(TaskBase):
    id: int
    completed: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class TaskAction(BaseModel):
    action: ActionType
    task_description: Optional[str] = Field(None, description="The task content or description")
    task_identifier: Optional[str] = Field(None, description="Keywords to identify which task to complete/modify")
    new_description: Optional[str] = Field(None, description="New description for task modification")
    reminder_interval: Optional[int] = Field(None, description="New reminder interval in minutes")
    priority_level: Optional[int] = Field(None, ge=1, le=5, description="Task priority level")
    suggested_category: Optional[TaskCategory] = None
    confidence: float = Field(description="Confidence score 0-1 of the interpretation")
    response_message: str = Field(description="Natural language response to speak back to user")
    clarification_needed: Optional[str] = Field(None, description="What clarification to ask if confidence is low")

class MultiTaskAction(BaseModel):
    """For handling multiple tasks in one command"""
    actions: List[TaskAction]
    summary_response: str = Field(description="Overall response summarizing all actions")

class VoiceCommandRequest(BaseModel):
    audio_data: str  # Base64 encoded audio
    
class VoiceCommandResponse(BaseModel):
    action: TaskAction
    success: bool
    message: str

class TTSRequest(BaseModel):
    text: str
    
class TTSResponse(BaseModel):
    audio_data: str  # Base64 encoded audio
    success: bool