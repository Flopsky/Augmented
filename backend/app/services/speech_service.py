import asyncio
import base64
import io
import wave
import numpy as np
from faster_whisper import WhisperModel
import logging
import os
import tempfile
import subprocess
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
        Supports multiple audio formats: WAV, WebM, OGG, MP3, etc.
        """
        try:
            if not self.whisper_model:
                logger.error("Whisper model not initialized")
                return None
            
            # Decode base64 audio data
            audio_bytes = base64.b64decode(audio_data)
            logger.info(f"Decoded audio data: {len(audio_bytes)} bytes")
            
            # Try to detect audio format and convert to numpy array
            audio_array = await self._bytes_to_numpy_flexible(audio_bytes)
            
            if audio_array is None:
                logger.error("Failed to convert audio bytes to numpy array")
                return None
            
            # Validate audio quality
            logger.info(f"Audio array shape: {audio_array.shape}, duration: {len(audio_array)/16000:.2f}s")
            logger.info(f"Audio stats - Min: {audio_array.min():.4f}, Max: {audio_array.max():.4f}, Mean: {audio_array.mean():.4f}")
            
            # Check if audio is too quiet (might be the issue)
            audio_max = np.abs(audio_array).max()
            if audio_max < 0.01:
                logger.warning(f"Audio seems very quiet (max amplitude: {audio_max:.4f}). This might cause poor transcription.")
            
            # Try different Whisper parameters for better transcription
            try:
                # First attempt with standard parameters
                segments, info = self.whisper_model.transcribe(
                    audio_array,
                    language="en",
                    beam_size=5,
                    best_of=5,
                    temperature=0.0,
                    condition_on_previous_text=False,  # Don't rely on previous context
                    compression_ratio_threshold=2.4,  # Default value
                    log_prob_threshold=-1.0,          # Default value
                    no_speech_threshold=0.6,          # Default value
                    initial_prompt=None               # No initial prompt
                )
                
                # Combine all segments
                transcription = " ".join([segment.text for segment in segments])
                
                # Log transcription details
                logger.info(f"Whisper detected language: {info.language} (probability: {info.language_probability:.2f})")
                logger.info(f"Number of segments: {len(list(segments))}")
                
                # If transcription is still poor, try with different parameters
                if transcription.strip().lower() in ["you", "yo", "", " "]:
                    logger.warning(f"Poor transcription result: '{transcription}'. Trying alternative parameters...")
                    
                    # Second attempt with different parameters
                    segments, info = self.whisper_model.transcribe(
                        audio_array,
                        language=None,  # Let Whisper detect language
                        beam_size=1,    # Faster, less accurate
                        temperature=0.5,  # Allow some creativity
                        condition_on_previous_text=False,
                        no_speech_threshold=0.3,  # Lower threshold
                        initial_prompt="This is a task management command about adding, completing, or listing tasks."
                    )
                    
                    alternative_transcription = " ".join([segment.text for segment in segments])
                    logger.info(f"Alternative transcription: '{alternative_transcription}'")
                    
                    # Use alternative if it's better
                    if len(alternative_transcription.strip()) > len(transcription.strip()):
                        transcription = alternative_transcription
                        logger.info("Using alternative transcription")
                
                logger.info(f"Final speech transcribed: '{transcription}'")
                return transcription.strip()
                
            except Exception as whisper_error:
                logger.error(f"Whisper transcription failed: {whisper_error}")
                return None
            
        except Exception as e:
            logger.error(f"Error in speech-to-text: {e}")
            return None
    
    async def _bytes_to_numpy_flexible(self, audio_bytes: bytes) -> Optional[np.ndarray]:
        """
        Convert audio bytes to numpy array supporting multiple formats
        Uses ffmpeg for format conversion when needed
        """
        # First, try WAV format (original approach)
        try:
            audio_array = self._bytes_to_numpy_wav(audio_bytes)
            logger.debug("Successfully processed as WAV format")
            return audio_array
        except Exception as wav_error:
            logger.debug(f"WAV processing failed: {wav_error}")
        
        # If WAV fails, try using ffmpeg for format conversion
        try:
            audio_array = await self._convert_audio_with_ffmpeg(audio_bytes)
            logger.debug("Successfully processed with ffmpeg conversion")
            return audio_array
        except Exception as ffmpeg_error:
            logger.error(f"FFmpeg conversion failed: {ffmpeg_error}")
        
        # Final fallback: try to interpret as raw PCM data
        try:
            logger.debug("Trying raw PCM fallback")
            audio_array = np.frombuffer(audio_bytes, dtype=np.int16)
            audio_array = audio_array.astype(np.float32) / 32768
            logger.debug(f"Raw PCM fallback successful: {len(audio_array)} samples")
            return audio_array
        except Exception as pcm_error:
            logger.error(f"Raw PCM fallback failed: {pcm_error}")
            return None
    
    def _bytes_to_numpy_wav(self, audio_bytes: bytes) -> np.ndarray:
        """
        Convert WAV audio bytes to numpy array (original implementation)
        """
        # Create a BytesIO object from the bytes
        audio_io = io.BytesIO(audio_bytes)
        
        # Open as wave file
        with wave.open(audio_io, 'rb') as wav_file:
            # Get audio parameters
            frames = wav_file.readframes(-1)
            sample_rate = wav_file.getframerate()
            channels = wav_file.getnchannels()
            sample_width = wav_file.getsampwidth()
            
            logger.debug(f"WAV info: sample_rate={sample_rate}, channels={channels}, sample_width={sample_width}")
            
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
    
    async def _convert_audio_with_ffmpeg(self, audio_bytes: bytes) -> np.ndarray:
        """
        Convert audio using ffmpeg to WAV format, then to numpy array
        This handles WebM, OGG, MP3, and other formats
        """
        with tempfile.NamedTemporaryFile(suffix='.webm', delete=False) as input_file:
            input_file.write(audio_bytes)
            input_file.flush()
            
            logger.info(f"Created temporary input file: {input_file.name} ({len(audio_bytes)} bytes)")
            
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as output_file:
                try:
                    # Convert to WAV using ffmpeg
                    cmd = [
                        'ffmpeg',
                        '-i', input_file.name,
                        '-acodec', 'pcm_s16le',  # 16-bit PCM
                        '-ar', '16000',          # 16kHz sample rate (Whisper's preferred)
                        '-ac', '1',              # Mono channel
                        '-y',                    # Overwrite output file
                        '-v', 'warning',         # Reduce verbosity but show warnings
                        output_file.name
                    ]
                    
                    logger.info(f"Running ffmpeg: {' '.join(cmd)}")
                    
                    # Run ffmpeg with error capture
                    result = subprocess.run(
                        cmd,
                        capture_output=True,
                        text=True,
                        check=True
                    )
                    
                    # Log ffmpeg output
                    if result.stderr:
                        logger.info(f"FFmpeg stderr: {result.stderr}")
                    if result.stdout:
                        logger.debug(f"FFmpeg stdout: {result.stdout}")
                    
                    # Check if output file was created and has content
                    if not os.path.exists(output_file.name):
                        raise RuntimeError("FFmpeg did not create output file")
                    
                    output_size = os.path.getsize(output_file.name)
                    logger.info(f"FFmpeg output file size: {output_size} bytes")
                    
                    if output_size == 0:
                        raise RuntimeError("FFmpeg created empty output file")
                    
                    # Read the converted WAV file
                    with open(output_file.name, 'rb') as wav_file:
                        wav_bytes = wav_file.read()
                    
                    logger.info(f"Read converted WAV file: {len(wav_bytes)} bytes")
                    
                    # Convert WAV to numpy array
                    audio_array = self._bytes_to_numpy_wav(wav_bytes)
                    
                    logger.info(f"FFmpeg conversion successful: {len(audio_array)} samples, {len(audio_array)/16000:.2f}s duration")
                    return audio_array
                    
                except subprocess.CalledProcessError as e:
                    logger.error(f"FFmpeg conversion failed with exit code {e.returncode}")
                    logger.error(f"FFmpeg stderr: {e.stderr}")
                    logger.error(f"FFmpeg stdout: {e.stdout}")
                    raise
                except Exception as e:
                    logger.error(f"FFmpeg conversion error: {e}")
                    raise
                finally:
                    # Clean up temporary files
                    try:
                        if os.path.exists(input_file.name):
                            os.unlink(input_file.name)
                            logger.debug(f"Cleaned up input file: {input_file.name}")
                        if os.path.exists(output_file.name):
                            os.unlink(output_file.name)
                            logger.debug(f"Cleaned up output file: {output_file.name}")
                    except Exception as cleanup_error:
                        logger.warning(f"Failed to clean up temporary files: {cleanup_error}")