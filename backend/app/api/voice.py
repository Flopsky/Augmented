from fastapi import APIRouter, Depends, HTTPException, status, Response
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
import base64
import io
from app.core.database import get_db
from app.models.schemas import (
    VoiceCommandRequest, VoiceCommandResponse, TTSRequest, TTSResponse,
    TaskAction, ActionType, TaskCreate, TaskUpdate
)
from app.services.claude_service import ClaudeService
from app.services.speech_service import SpeechService
from app.services.tts_service import get_tts_service
from app.services.task_service import TaskService
import logging
import asyncio

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/voice", tags=["voice"])

# Initialize services
claude_service = ClaudeService()
speech_service = SpeechService()

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
        
        # Step 5: Generate TTS response if available
        tts_service = await get_tts_service()
        audio_data = await tts_service.synthesize_speech(action.response_message)
        
        # If TTS fails, still return success but without audio
        if not audio_data:
            logger.warning("TTS generation failed, continuing without audio")
        
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
    """Convert text to speech using Kokoro-TTS"""
    try:
        tts_service = await get_tts_service()
        audio_data = await tts_service.synthesize_speech(request.text)
        
        if audio_data:
            # Convert bytes to base64 for JSON response
            audio_base64 = base64.b64encode(audio_data).decode('utf-8')
            return TTSResponse(
                audio_data=audio_base64,
                success=True
            )
        else:
            return TTSResponse(
                audio_data="",
                success=False
            )
        
    except Exception as e:
        logger.error(f"Error in text-to-speech: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to convert text to speech"
        )

@router.get("/tts/{text}")
async def get_text_to_speech_audio(text: str, voice: str = "af_bella", speed: float = 1.0):
    """
    Generate and return audio directly as MP3 stream
    This endpoint is compatible with frontend audio players
    """
    try:
        tts_service = await get_tts_service()
        audio_data = await tts_service.synthesize_speech(text, voice=voice, speed=speed)
        
        if audio_data:
            return Response(
                content=audio_data,
                media_type="audio/mpeg",
                headers={
                    "Content-Disposition": f"inline; filename=\"tts_{hash(text)}.mp3\"",
                    "Cache-Control": "public, max-age=3600"  # Cache for 1 hour
                }
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="TTS service unavailable or text synthesis failed"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating TTS audio: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate audio"
        )

@router.get("/voices")
async def get_available_voices():
    """Get list of available TTS voices"""
    try:
        tts_service = await get_tts_service()
        voices_info = await tts_service.get_available_voices()
        
        return {
            "voices": voices_info["voices"],
            "default_voice": tts_service.get_default_voice(),
            "source": voices_info["source"],
            "tts_available": await tts_service.check_availability()
        }
        
    except Exception as e:
        logger.error(f"Error getting available voices: {e}")
        return {
            "voices": ["af_bella"],  # Fallback
            "default_voice": "af_bella",
            "source": "fallback",
            "tts_available": False
        }

@router.get("/tts/status")
async def get_tts_status():
    """Check TTS service status and availability"""
    try:
        tts_service = await get_tts_service()
        is_available = await tts_service.check_availability()
        
        return {
            "available": is_available,
            "service": "kokoro-tts",
            "base_url": tts_service.kokoro_base_url,
            "default_voice": tts_service.get_default_voice(),
            "cache_enabled": True
        }
        
    except Exception as e:
        logger.error(f"Error checking TTS status: {e}")
        return {
            "available": False,
            "service": "kokoro-tts",
            "error": str(e)
        }

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