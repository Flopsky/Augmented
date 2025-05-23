"""
Text-to-Speech service using Kokoro-TTS via FastAPI
Handles voice synthesis and caching for the task reminder application
"""

import asyncio
import aiofiles
import hashlib
import os
import tempfile
from typing import Optional, Dict, Any
import httpx
from pathlib import Path
from app.core.logging import get_logger, LoggerMixin, log_async_function_call

logger = get_logger(__name__)

class TTSService(LoggerMixin):
    """Text-to-Speech service using Kokoro-TTS"""
    
    def __init__(self):
        self.kokoro_base_url = os.getenv("KOKORO_BASE_URL", "http://localhost:8880")
        self.default_voice = os.getenv("TTS_DEFAULT_VOICE", "af_bella")
        self.cache_dir = Path(tempfile.gettempdir()) / "tts_cache"
        self.cache_dir.mkdir(exist_ok=True)
        self.available_voices = [
            "af_bella",      # American female, warm tones
            "af_sarah",      # American female, clear articulation  
            "af_nicole",     # American female, dynamic range
            "af_sky",        # American female, youthful energy
            "am_adam",       # American male, natural inflection
            "am_michael",    # American male, deeper tones
            "bf_emma",       # British female
            "bf_isabella",   # British female, soft tones
            "bm_george",     # British male
            "bm_lewis",      # British male, mature tone
        ]
        self.client = httpx.AsyncClient(timeout=30.0)
        self._is_available = None
        
        self.logger.info(f"TTS Service initialized - Base URL: {self.kokoro_base_url}")
        self.logger.info(f"Default voice: {self.default_voice}")
        self.logger.info(f"Cache directory: {self.cache_dir}")
        self.logger.debug(f"Available voices: {', '.join(self.available_voices)}")
        
    async def __aenter__(self):
        self.logger.debug("Entering TTS service context")
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self.logger.debug("Exiting TTS service context")
        await self.client.aclose()
    
    @log_async_function_call
    async def check_availability(self) -> bool:
        """Check if Kokoro-TTS service is available"""
        if self._is_available is not None:
            self.logger.debug(f"Using cached availability status: {self._is_available}")
            return self._is_available
            
        try:
            self.logger.debug(f"Checking TTS service availability at {self.kokoro_base_url}")
            response = await self.client.get(f"{self.kokoro_base_url}/v1/audio/voices")
            self._is_available = response.status_code == 200
            
            if self._is_available:
                self.logger.info("Kokoro-TTS service is available")
            else:
                self.logger.warning(f"Kokoro-TTS service returned status {response.status_code}")
                
        except Exception as e:
            self.logger.error(f"Failed to connect to Kokoro-TTS service: {e}")
            self._is_available = False
            
        return self._is_available
    
    def _get_cache_key(self, text: str, voice: str, speed: float = 1.0) -> str:
        """Generate cache key for TTS request"""
        content = f"{text}_{voice}_{speed}"
        cache_key = hashlib.md5(content.encode()).hexdigest()
        self.logger.debug(f"Generated cache key: {cache_key} for text: '{text[:50]}...'")
        return cache_key
    
    def _get_cache_path(self, cache_key: str) -> Path:
        """Get cache file path for given cache key"""
        return self.cache_dir / f"{cache_key}.mp3"
    
    async def _load_from_cache(self, cache_key: str) -> Optional[bytes]:
        """Load audio from cache if available"""
        cache_path = self._get_cache_path(cache_key)
        if cache_path.exists():
            try:
                async with aiofiles.open(cache_path, 'rb') as f:
                    audio_data = await f.read()
                self.logger.info(f"Loaded audio from cache: {cache_key} ({len(audio_data)} bytes)")
                return audio_data
            except Exception as e:
                self.logger.error(f"Failed to load from cache: {e}")
                # Remove corrupted cache file
                try:
                    cache_path.unlink()
                    self.logger.warning(f"Removed corrupted cache file: {cache_path}")
                except Exception as cleanup_error:
                    self.logger.error(f"Failed to remove corrupted cache file: {cleanup_error}")
        return None
    
    async def _save_to_cache(self, cache_key: str, audio_data: bytes) -> None:
        """Save audio data to cache"""
        cache_path = self._get_cache_path(cache_key)
        try:
            async with aiofiles.open(cache_path, 'wb') as f:
                await f.write(audio_data)
            self.logger.info(f"Saved audio to cache: {cache_key} ({len(audio_data)} bytes)")
        except Exception as e:
            self.logger.error(f"Failed to save to cache: {e}")
    
    @log_async_function_call
    async def synthesize_speech(
        self, 
        text: str, 
        voice: Optional[str] = None,
        speed: float = 1.0,
        use_cache: bool = True
    ) -> Optional[bytes]:
        """
        Synthesize speech from text using Kokoro-TTS
        
        Args:
            text: Text to synthesize
            voice: Voice to use (defaults to service default)
            speed: Speech speed multiplier (0.5-2.0)
            use_cache: Whether to use caching
            
        Returns:
            Audio data as bytes (MP3 format) or None if failed
        """
        if not text or not text.strip():
            self.logger.warning("Empty text provided for TTS")
            return None
            
        # Validate and set voice
        voice = voice or self.default_voice
        if voice not in self.available_voices:
            self.logger.warning(f"Unknown voice '{voice}', using default '{self.default_voice}'")
            voice = self.default_voice
        
        # Clamp speed to reasonable range
        original_speed = speed
        speed = max(0.5, min(2.0, speed))
        if speed != original_speed:
            self.logger.warning(f"Speed clamped from {original_speed} to {speed}")
        
        self.logger.info(f"Synthesizing speech: '{text[:100]}...' (voice: {voice}, speed: {speed})")
        
        # Check cache first
        cache_key = self._get_cache_key(text, voice, speed)
        if use_cache:
            cached_audio = await self._load_from_cache(cache_key)
            if cached_audio:
                return cached_audio
        
        # Check if service is available
        if not await self.check_availability():
            self.logger.error("Kokoro-TTS service is not available")
            return None
        
        try:
            # Prepare request data
            request_data = {
                "model": "kokoro",
                "input": text,
                "voice": voice,
                "response_format": "mp3",
                "speed": speed
            }
            
            # Make request to Kokoro-TTS
            self.logger.debug(f"Making TTS request to {self.kokoro_base_url}/v1/audio/speech")
            response = await self.client.post(
                f"{self.kokoro_base_url}/v1/audio/speech",
                json=request_data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                audio_data = response.content
                
                # Save to cache
                if use_cache:
                    await self._save_to_cache(cache_key, audio_data)
                
                self.logger.info(f"Successfully generated TTS audio ({len(audio_data)} bytes)")
                return audio_data
            else:
                self.logger.error(f"TTS request failed with status {response.status_code}: {response.text}")
                return None
                
        except Exception as e:
            self.logger.error(f"Error during TTS synthesis: {e}")
            return None
    
    @log_async_function_call
    async def get_available_voices(self) -> Dict[str, Any]:
        """Get list of available voices from Kokoro-TTS service"""
        try:
            if not await self.check_availability():
                self.logger.warning("TTS service unavailable, returning fallback voices")
                return {"voices": self.available_voices, "source": "fallback"}
            
            response = await self.client.get(f"{self.kokoro_base_url}/v1/audio/voices")
            if response.status_code == 200:
                data = response.json()
                voices = data.get("voices", self.available_voices)
                self.logger.info(f"Retrieved {len(voices)} voices from TTS service")
                return {"voices": voices, "source": "service"}
            else:
                self.logger.warning(f"Failed to get voices from service (status {response.status_code}), using fallback")
                return {"voices": self.available_voices, "source": "fallback"}
                
        except Exception as e:
            self.logger.error(f"Error getting available voices: {e}")
            return {"voices": self.available_voices, "source": "fallback"}
    
    def get_default_voice(self) -> str:
        """Get the default voice for TTS"""
        return self.default_voice
    
    @log_async_function_call
    async def cleanup_cache(self, max_age_hours: int = 24) -> None:
        """Clean up old cache files"""
        try:
            import time
            current_time = time.time()
            max_age_seconds = max_age_hours * 3600
            
            cleaned_count = 0
            total_size = 0
            
            for cache_file in self.cache_dir.glob("*.mp3"):
                file_age = current_time - cache_file.stat().st_mtime
                if file_age > max_age_seconds:
                    file_size = cache_file.stat().st_size
                    cache_file.unlink()
                    cleaned_count += 1
                    total_size += file_size
            
            if cleaned_count > 0:
                self.logger.info(f"Cleaned up {cleaned_count} old cache files ({total_size / 1024 / 1024:.2f} MB)")
            else:
                self.logger.debug("No cache files needed cleanup")
                
        except Exception as e:
            self.logger.error(f"Error during cache cleanup: {e}")

# Global TTS service instance
tts_service = TTSService()

async def get_tts_service() -> TTSService:
    """Get the global TTS service instance"""
    return tts_service 