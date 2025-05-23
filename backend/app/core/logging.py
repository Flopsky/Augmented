"""
Logging configuration for the Task Reminder application
Provides structured logging with different levels and formatters
"""

import logging
import logging.handlers
import os
import sys
from pathlib import Path
from typing import Optional

def setup_logging(
    log_level: str = "INFO",
    log_file: Optional[str] = None,
    log_dir: str = "logs",
    max_bytes: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5,
    enable_console: bool = True,
    enable_file: bool = True
) -> None:
    """
    Setup comprehensive logging configuration
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Log file name (defaults to app.log)
        log_dir: Directory for log files
        max_bytes: Maximum size of log file before rotation
        backup_count: Number of backup files to keep
        enable_console: Whether to enable console logging
        enable_file: Whether to enable file logging
    """
    
    # Convert string level to logging constant
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)
    
    # Create log directory if it doesn't exist
    if enable_file:
        log_path = Path(log_dir)
        log_path.mkdir(exist_ok=True)
        
        if log_file is None:
            log_file = "app.log"
        
        full_log_path = log_path / log_file
    
    # Create root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)
    
    # Clear existing handlers
    root_logger.handlers.clear()
    
    # Create formatters
    detailed_formatter = logging.Formatter(
        fmt='%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(funcName)s() - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    simple_formatter = logging.Formatter(
        fmt='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%H:%M:%S'
    )
    
    # Console handler
    if enable_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(numeric_level)
        console_handler.setFormatter(simple_formatter)
        root_logger.addHandler(console_handler)
    
    # File handler with rotation
    if enable_file:
        file_handler = logging.handlers.RotatingFileHandler(
            filename=full_log_path,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding='utf-8'
        )
        file_handler.setLevel(numeric_level)
        file_handler.setFormatter(detailed_formatter)
        root_logger.addHandler(file_handler)
    
    # Set specific logger levels for third-party libraries
    logging.getLogger("uvicorn").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("fastapi").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("anthropic").setLevel(logging.WARNING)
    
    # Log the configuration
    logger = logging.getLogger(__name__)
    logger.info(f"Logging configured - Level: {log_level}, Console: {enable_console}, File: {enable_file}")
    if enable_file:
        logger.info(f"Log file: {full_log_path}")

def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with the given name
    
    Args:
        name: Logger name (usually __name__)
        
    Returns:
        Configured logger instance
    """
    return logging.getLogger(name)

class LoggerMixin:
    """
    Mixin class to add logging capabilities to any class
    """
    
    @property
    def logger(self) -> logging.Logger:
        """Get logger for this class"""
        return logging.getLogger(f"{self.__class__.__module__}.{self.__class__.__name__}")

def log_function_call(func):
    """
    Decorator to log function calls with parameters and execution time
    """
    import functools
    import time
    
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        logger = logging.getLogger(func.__module__)
        start_time = time.time()
        
        # Log function entry
        logger.debug(f"Calling {func.__name__} with args={args}, kwargs={kwargs}")
        
        try:
            result = func(*args, **kwargs)
            execution_time = time.time() - start_time
            logger.debug(f"{func.__name__} completed in {execution_time:.3f}s")
            return result
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"{func.__name__} failed after {execution_time:.3f}s: {e}")
            raise
    
    return wrapper

def log_async_function_call(func):
    """
    Decorator to log async function calls with parameters and execution time
    """
    import functools
    import time
    import asyncio
    
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        logger = logging.getLogger(func.__module__)
        start_time = time.time()
        
        # Log function entry
        logger.debug(f"Calling async {func.__name__} with args={args}, kwargs={kwargs}")
        
        try:
            result = await func(*args, **kwargs)
            execution_time = time.time() - start_time
            logger.debug(f"Async {func.__name__} completed in {execution_time:.3f}s")
            return result
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"Async {func.__name__} failed after {execution_time:.3f}s: {e}")
            raise
    
    return wrapper

# Environment-based configuration
def configure_logging_from_env():
    """
    Configure logging based on environment variables
    """
    log_level = os.getenv("LOG_LEVEL", "INFO")
    log_file = os.getenv("LOG_FILE")
    log_dir = os.getenv("LOG_DIR", "logs")
    enable_console = os.getenv("LOG_CONSOLE", "true").lower() == "true"
    enable_file = os.getenv("LOG_FILE_ENABLED", "true").lower() == "true"
    
    setup_logging(
        log_level=log_level,
        log_file=log_file,
        log_dir=log_dir,
        enable_console=enable_console,
        enable_file=enable_file
    ) 