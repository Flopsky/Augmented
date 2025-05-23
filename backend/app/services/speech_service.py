import asyncio
import base64
import io
import wave
import numpy as np
from faster_whisper import WhisperModel
import logging
import os
from typing import Optional

logger = logging.getLogger(__name__)

class SpeechService:
    def __init__(self):
        self.whisper_model = None
        self._initialize_whisper()
    
    def _initialize_whisper(self):
        """Initialize Whisper model for speech-to-text"""
        try:
            # Use a smaller model for faster processing
            model_size = os.getenv("WHISPER_MODEL_SIZE", "base")
            self.whisper_model = WhisperModel(model_size, device="cpu", compute_type="int8")
            logger.info(f"Whisper model '{model_size}' initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Whisper model: {e}")
            self.whisper_model = None
    
    async def speech_to_text(self, audio_data: str) -> Optional[str]:
        """
        Convert base64 encoded audio to text using faster-whisper
        """
        try:
            if not self.whisper_model:
                logger.error("Whisper model not initialized")
                return None
            
            # Decode base64 audio data
            audio_bytes = base64.b64decode(audio_data)
            
            # Convert to numpy array (assuming WAV format)
            audio_array = self._bytes_to_numpy(audio_bytes)
            
            # Transcribe using faster-whisper
            segments, info = self.whisper_model.transcribe(
                audio_array,
                language="en",
                beam_size=5,
                best_of=5,
                temperature=0.0
            )
            
            # Combine all segments
            transcription = " ".join([segment.text for segment in segments])
            
            logger.info(f"Speech transcribed: {transcription}")
            return transcription.strip()
            
        except Exception as e:
            logger.error(f"Error in speech-to-text: {e}")
            return None
    
    def _bytes_to_numpy(self, audio_bytes: bytes) -> np.ndarray:
        """
        Convert audio bytes to numpy array
        """
        try:
            # Create a BytesIO object from the bytes
            audio_io = io.BytesIO(audio_bytes)
            
            # Open as wave file
            with wave.open(audio_io, 'rb') as wav_file:
                # Get audio parameters
                frames = wav_file.readframes(-1)
                sample_rate = wav_file.getframerate()
                channels = wav_file.getnchannels()
                sample_width = wav_file.getsampwidth()
                
                # Convert to numpy array
                if sample_width == 1:
                    dtype = np.uint8
                elif sample_width == 2:
                    dtype = np.int16
                elif sample_width == 4:
                    dtype = np.int32
                else:
                    raise ValueError(f"Unsupported sample width: {sample_width}")
                
                audio_array = np.frombuffer(frames, dtype=dtype)
                
                # Convert to float32 and normalize
                if dtype == np.uint8:
                    audio_array = (audio_array.astype(np.float32) - 128) / 128
                elif dtype == np.int16:
                    audio_array = audio_array.astype(np.float32) / 32768
                elif dtype == np.int32:
                    audio_array = audio_array.astype(np.float32) / 2147483648
                
                # Handle stereo by taking the first channel
                if channels == 2:
                    audio_array = audio_array[::2]
                
                return audio_array
                
        except Exception as e:
            logger.error(f"Error converting bytes to numpy: {e}")
            # Fallback: try to interpret as raw PCM data
            try:
                audio_array = np.frombuffer(audio_bytes, dtype=np.int16)
                return audio_array.astype(np.float32) / 32768
            except:
                raise ValueError("Could not convert audio bytes to numpy array")

class TTSService:
    def __init__(self):
        self.tts_available = False
        self._initialize_tts()
    
    def _initialize_tts(self):
        """Initialize TTS service (placeholder for kokoro-tts)"""
        try:
            # For now, we'll use a simple placeholder
            # In a real implementation, you would initialize kokoro-tts here
            self.tts_available = True
            logger.info("TTS service initialized (placeholder)")
        except Exception as e:
            logger.error(f"Failed to initialize TTS: {e}")
            self.tts_available = False
    
    async def text_to_speech(self, text: str) -> Optional[str]:
        """
        Convert text to speech and return base64 encoded audio
        For now, this is a placeholder that returns None
        """
        try:
            if not self.tts_available:
                logger.warning("TTS service not available")
                return None
            
            # Placeholder implementation
            # In a real implementation, you would use kokoro-tts here
            logger.info(f"TTS request for text: {text}")
            
            # For now, return None to indicate TTS is not implemented
            # The frontend will handle this gracefully
            return None
            
        except Exception as e:
            logger.error(f"Error in text-to-speech: {e}")
            return None