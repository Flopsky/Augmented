from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.schemas import (
    VoiceCommandRequest, VoiceCommandResponse, TTSRequest, TTSResponse,
    TaskAction, ActionType, TaskCreate, TaskUpdate
)
from app.services.claude_service import ClaudeService
from app.services.speech_service import SpeechService, TTSService
from app.services.task_service import TaskService
import logging
import asyncio

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/voice", tags=["voice"])

# Initialize services
claude_service = ClaudeService()
speech_service = SpeechService()
tts_service = TTSService()

@router.post("/process-command", response_model=VoiceCommandResponse)
async def process_voice_command(
    request: VoiceCommandRequest,
    db: Session = Depends(get_db)
):
    """Process a voice command through the complete pipeline"""
    try:
        # Step 1: Convert speech to text
        text = await speech_service.speech_to_text(request.audio_data)
        if not text:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Could not transcribe audio"
            )
        
        logger.info(f"Transcribed text: {text}")
        
        # Step 2: Get current tasks for context
        task_service = TaskService(db)
        current_tasks = task_service.get_tasks_dict()
        
        # Step 3: Process with Claude
        action = await claude_service.process_user_command(text, current_tasks)
        
        # Step 4: Execute the action
        success = await execute_task_action(action, task_service)
        
        return VoiceCommandResponse(
            action=action,
            success=success,
            message=action.response_message
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing voice command: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process voice command"
        )

@router.post("/speech-to-text")
async def speech_to_text(request: VoiceCommandRequest):
    """Convert speech to text"""
    try:
        text = await speech_service.speech_to_text(request.audio_data)
        if not text:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Could not transcribe audio"
            )
        
        return {"text": text, "success": True}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in speech-to-text: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to convert speech to text"
        )

@router.post("/text-to-speech", response_model=TTSResponse)
async def text_to_speech(request: TTSRequest):
    """Convert text to speech"""
    try:
        audio_data = await tts_service.text_to_speech(request.text)
        
        return TTSResponse(
            audio_data=audio_data or "",
            success=audio_data is not None
        )
        
    except Exception as e:
        logger.error(f"Error in text-to-speech: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to convert text to speech"
        )

@router.post("/process-text")
async def process_text_command(
    text: str,
    db: Session = Depends(get_db)
):
    """Process a text command (for testing without audio)"""
    try:
        # Get current tasks for context
        task_service = TaskService(db)
        current_tasks = task_service.get_tasks_dict()
        
        # Process with Claude
        action = await claude_service.process_user_command(text, current_tasks)
        
        # Execute the action
        success = await execute_task_action(action, task_service)
        
        return {
            "action": action.dict(),
            "success": success,
            "message": action.response_message
        }
        
    except Exception as e:
        logger.error(f"Error processing text command: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process text command"
        )

async def execute_task_action(action: TaskAction, task_service: TaskService) -> bool:
    """Execute a task action based on the parsed intent"""
    try:
        if action.action == ActionType.ADD_TASK:
            if not action.task_description:
                return False
            
            task_create = TaskCreate(
                description=action.task_description,
                priority=action.priority_level or 3,
                category=action.suggested_category
            )
            task_service.create_task(task_create)
            return True
        
        elif action.action == ActionType.COMPLETE_TASK:
            if not action.task_identifier:
                return False
            
            # Find task using fuzzy matching
            task = task_service.find_task_by_description(action.task_identifier)
            if task:
                task_service.complete_task(task.id)
                return True
            return False
        
        elif action.action == ActionType.MODIFY_TASK:
            if not action.task_identifier:
                return False
            
            # Find task using fuzzy matching
            task = task_service.find_task_by_description(action.task_identifier)
            if task and action.new_description:
                task_update = TaskUpdate(description=action.new_description)
                task_service.update_task(task.id, task_update)
                return True
            return False
        
        elif action.action == ActionType.CLEAR_COMPLETED:
            task_service.clear_completed_tasks()
            return True
        
        elif action.action == ActionType.LIST_TASKS:
            # This is handled by returning the action, frontend will display tasks
            return True
        
        elif action.action == ActionType.UNCLEAR:
            # No action needed, just return the clarification
            return True
        
        else:
            logger.warning(f"Unknown action type: {action.action}")
            return False
            
    except Exception as e:
        logger.error(f"Error executing task action: {e}")
        return False