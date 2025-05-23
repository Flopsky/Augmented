from fastapi import APIRouter, Depends, HTTPException, status, Response
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
import base64
import io
from app.core.database import get_db
from app.core.logging import get_logger, log_async_function_call
from app.models.schemas import (
    VoiceCommandRequest, VoiceCommandResponse, TTSRequest, TTSResponse,
    TaskAction, ActionType, TaskCreate, TaskUpdate
)
from app.services.claude_service import ClaudeService
from app.services.speech_service import SpeechService
from app.services.tts_service import get_tts_service
from app.services.task_service import TaskService
import asyncio

logger = get_logger(__name__)

router = APIRouter(prefix="/api/voice", tags=["voice"])

# Initialize services
claude_service = ClaudeService()
speech_service = SpeechService()

@router.post("/process-command", response_model=VoiceCommandResponse)
@log_async_function_call
async def process_voice_command(
    request: VoiceCommandRequest,
    db: Session = Depends(get_db)
):
    """Process a voice command through the complete pipeline"""
    try:
        logger.info("Processing voice command")
        
        # Step 1: Convert speech to text
        logger.debug("Step 1: Converting speech to text")
        text = await speech_service.speech_to_text(request.audio_data)
        if not text:
            logger.warning("Speech-to-text conversion failed")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Could not transcribe audio"
            )
        
        logger.info(f"Transcribed text: '{text}'")
        
        # Step 2: Get current tasks for context
        logger.debug("Step 2: Getting current tasks for context")
        task_service = TaskService(db)
        current_tasks = task_service.get_tasks_dict()
        logger.debug(f"Retrieved {len(current_tasks)} tasks for context")
        
        # Step 3: Process with Claude
        logger.debug("Step 3: Processing with Claude")
        action = await claude_service.process_user_command(text, current_tasks)
        logger.info(f"Claude processed command - Action: {action.action}, Confidence: {action.confidence}")
        
        # Step 4: Execute the action
        logger.debug("Step 4: Executing task action")
        success = await execute_task_action(action, task_service)
        logger.info(f"Task action executed - Success: {success}")
        
        # Step 5: Generate TTS response if available
        logger.debug("Step 5: Generating TTS response")
        tts_service = await get_tts_service()
        audio_data = await tts_service.synthesize_speech(action.response_message)
        
        # If TTS fails, still return success but without audio
        if not audio_data:
            logger.warning("TTS generation failed, continuing without audio")
        else:
            logger.info("TTS response generated successfully")
        
        logger.info("Voice command processing completed successfully")
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
@log_async_function_call
async def speech_to_text(request: VoiceCommandRequest):
    """Convert speech to text"""
    try:
        logger.info("Processing speech-to-text request")
        text = await speech_service.speech_to_text(request.audio_data)
        if not text:
            logger.warning("Speech-to-text conversion failed")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Could not transcribe audio"
            )
        
        logger.info(f"Speech-to-text successful: '{text}'")
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
@log_async_function_call
async def text_to_speech(request: TTSRequest):
    """Convert text to speech using Kokoro-TTS"""
    try:
        logger.info(f"Processing text-to-speech request for: '{request.text[:50]}...'")
        tts_service = await get_tts_service()
        audio_data = await tts_service.synthesize_speech(request.text)
        
        if audio_data:
            # Convert bytes to base64 for JSON response
            audio_base64 = base64.b64encode(audio_data).decode('utf-8')
            logger.info(f"TTS successful - Generated {len(audio_data)} bytes of audio")
            return TTSResponse(
                audio_data=audio_base64,
                success=True
            )
        else:
            logger.warning("TTS generation failed")
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
@log_async_function_call
async def get_text_to_speech_audio(text: str, voice: str = "af_bella", speed: float = 1.0):
    """
    Generate and return audio directly as MP3 stream
    This endpoint is compatible with frontend audio players
    """
    try:
        logger.info(f"Generating TTS audio stream for: '{text[:50]}...' (voice: {voice}, speed: {speed})")
        tts_service = await get_tts_service()
        audio_data = await tts_service.synthesize_speech(text, voice=voice, speed=speed)
        
        if audio_data:
            logger.info(f"TTS audio stream generated successfully ({len(audio_data)} bytes)")
            return Response(
                content=audio_data,
                media_type="audio/mpeg",
                headers={
                    "Content-Disposition": f"inline; filename=\"tts_{hash(text)}.mp3\"",
                    "Cache-Control": "public, max-age=3600"  # Cache for 1 hour
                }
            )
        else:
            logger.warning("TTS audio stream generation failed")
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
@log_async_function_call
async def get_available_voices():
    """Get list of available TTS voices"""
    try:
        logger.debug("Getting available TTS voices")
        tts_service = await get_tts_service()
        voices_info = await tts_service.get_available_voices()
        
        logger.info(f"Retrieved {len(voices_info['voices'])} voices from {voices_info['source']}")
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
@log_async_function_call
async def get_tts_status():
    """Check TTS service status and availability"""
    try:
        logger.debug("Checking TTS service status")
        tts_service = await get_tts_service()
        is_available = await tts_service.check_availability()
        
        status_info = {
            "available": is_available,
            "service": "kokoro-tts",
            "base_url": tts_service.kokoro_base_url,
            "default_voice": tts_service.get_default_voice(),
            "cache_enabled": True
        }
        
        logger.info(f"TTS status check - Available: {is_available}")
        return status_info
        
    except Exception as e:
        logger.error(f"Error checking TTS status: {e}")
        return {
            "available": False,
            "service": "kokoro-tts",
            "error": str(e)
        }

@router.post("/process-text")
@log_async_function_call
async def process_text_command(
    text: str,
    db: Session = Depends(get_db)
):
    """Process a text command (for testing without audio)"""
    try:
        logger.info(f"Processing text command: '{text}'")
        
        # Get current tasks for context
        task_service = TaskService(db)
        current_tasks = task_service.get_tasks_dict()
        logger.debug(f"Retrieved {len(current_tasks)} tasks for context")
        
        # Process with Claude
        action = await claude_service.process_user_command(text, current_tasks)
        logger.info(f"Claude processed text command - Action: {action.action}, Confidence: {action.confidence}")
        
        # Execute the action
        success = await execute_task_action(action, task_service)
        logger.info(f"Text command executed - Success: {success}")
        
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
        logger.debug(f"Executing task action: {action.action}")
        
        if action.action == ActionType.ADD_TASK:
            if not action.task_description:
                logger.warning("ADD_TASK action missing task description")
                return False
            
            task_create = TaskCreate(
                description=action.task_description,
                priority=action.priority_level or 3,
                category=action.suggested_category
            )
            new_task = task_service.create_task(task_create)
            logger.info(f"Created new task: {new_task.id} - '{new_task.description}'")
            return True
        
        elif action.action == ActionType.COMPLETE_TASK:
            if not action.task_identifier:
                logger.warning("COMPLETE_TASK action missing task identifier")
                return False
            
            # Find task using fuzzy matching
            task = task_service.find_task_by_description(action.task_identifier)
            if task:
                task_service.complete_task(task.id)
                logger.info(f"Completed task: {task.id} - '{task.description}'")
                return True
            else:
                logger.warning(f"Could not find task matching: '{action.task_identifier}'")
                return False
        
        elif action.action == ActionType.MODIFY_TASK:
            if not action.task_identifier:
                logger.warning("MODIFY_TASK action missing task identifier")
                return False
            
            # Find task using fuzzy matching
            task = task_service.find_task_by_description(action.task_identifier)
            if task and action.new_description:
                task_update = TaskUpdate(description=action.new_description)
                updated_task = task_service.update_task(task.id, task_update)
                logger.info(f"Modified task: {task.id} - '{task.description}' -> '{updated_task.description}'")
                return True
            else:
                logger.warning(f"Could not modify task: '{action.task_identifier}'")
                return False
        
        elif action.action == ActionType.CLEAR_COMPLETED:
            cleared_count = task_service.clear_completed_tasks()
            logger.info(f"Cleared {cleared_count} completed tasks")
            return True
        
        elif action.action == ActionType.LIST_TASKS:
            # This is handled by returning the action, frontend will display tasks
            logger.debug("LIST_TASKS action - no backend action needed")
            return True
        
        elif action.action == ActionType.UNCLEAR:
            # No action needed, just return the clarification
            logger.debug("UNCLEAR action - no backend action needed")
            return True
        
        else:
            logger.warning(f"Unknown action type: {action.action}")
            return False
            
    except Exception as e:
        logger.error(f"Error executing task action: {e}")
        return False