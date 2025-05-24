import instructor
from anthropic import Anthropic
from app.models.schemas import TaskAction, ActionType
from typing import List, Dict
import json
import os
import logging

logger = logging.getLogger(__name__)

class ClaudeService:
    def __init__(self):
        api_key = os.getenv("ANTHROPIC_API_KEY")
        self.api_available = False
        
        if not api_key or api_key == "sk-ant-placeholder-key-for-development":
            logger.warning("ANTHROPIC_API_KEY not set or using placeholder. Claude features will use fallback mode.")
            self.client = None
        else:
            try:
                self.client = instructor.from_anthropic(Anthropic(api_key=api_key))
                self.api_available = True
                logger.info("Claude API initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Claude API: {e}")
                self.client = None
    
    async def process_user_command(self, user_input: str, current_tasks: List[Dict]) -> TaskAction:
        """
        Send user input to Claude Sonnet with context about current tasks
        """
        # Use fallback if Claude API is not available
        if not self.api_available or not self.client:
            logger.info("Using fallback keyword matching (Claude API not available)")
            return self._fallback_keyword_matching(user_input, current_tasks)
        
        try:
            system_prompt = f"""
            You are a task management assistant. Interpret the user's command and return structured data.
            
            Current tasks:
            {json.dumps(current_tasks, indent=2)}
            
            Guidelines:
            - For ADD_TASK: Extract the exact task description
            - For COMPLETE_TASK: Match against existing tasks using fuzzy logic
            - For MODIFY_TASK: Identify which task and what changes
            - Set confidence based on how clear the intent is (0.0 to 1.0)
            - Generate a natural, conversational response
            - If unclear, set action to UNCLEAR and provide clarification_needed
            - For task completion, use keywords from the user input to match existing tasks
            - Be helpful and encouraging in your responses
            - If user says things like "I'm done with X" or "finished X", treat as COMPLETE_TASK
            - For listing tasks, use LIST_TASKS action
            
            Examples:
            - "Add buy milk" -> ADD_TASK with task_description="buy milk"
            - "I finished the groceries" -> COMPLETE_TASK with task_identifier="groceries"
            - "What's on my list?" -> LIST_TASKS
            - "Change the meeting to 3 PM" -> MODIFY_TASK with task_identifier="meeting" and new_description="meeting at 3 PM"
            """
            
            response = self.client.chat.completions.create(
                model="claude-3-sonnet-20240229",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_input}
                ],
                response_model=TaskAction,
                max_tokens=1000,
                temperature=0.3
            )
            
            logger.info(f"Claude processed command: {user_input} -> {response.action}")
            return response
            
        except Exception as e:
            logger.error(f"Error processing command with Claude: {e}")
            # Fallback to keyword matching
            logger.info("Falling back to keyword matching")
            return self._fallback_keyword_matching(user_input, current_tasks)
    
    def _fallback_keyword_matching(self, user_input: str, current_tasks: List[Dict]) -> TaskAction:
        """
        Simple keyword-based fallback when Claude API fails
        """
        user_lower = user_input.lower()
        
        # Simple keyword matching
        if any(word in user_lower for word in ["add", "create", "new"]):
            # Extract task description (simple approach)
            task_desc = user_input
            for word in ["add", "create", "new", "task"]:
                task_desc = task_desc.replace(word, "").strip()
            
            return TaskAction(
                action=ActionType.ADD_TASK,
                task_description=task_desc,
                confidence=0.7,
                response_message=f"I've added '{task_desc}' to your tasks."
            )
        
        elif any(word in user_lower for word in ["done", "finished", "complete", "completed"]):
            return TaskAction(
                action=ActionType.COMPLETE_TASK,
                task_identifier=user_input,
                confidence=0.6,
                response_message="I'll mark that task as complete."
            )
        
        elif any(word in user_lower for word in ["list", "show", "what", "tasks"]):
            return TaskAction(
                action=ActionType.LIST_TASKS,
                confidence=0.8,
                response_message="Here are your current tasks."
            )
        
        else:
            return TaskAction(
                action=ActionType.UNCLEAR,
                confidence=0.0,
                response_message="I didn't understand that. Could you please try again?",
                clarification_needed="Please tell me if you want to add, complete, or list tasks."
            )