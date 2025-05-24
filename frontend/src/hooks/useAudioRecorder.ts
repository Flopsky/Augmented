import { useState, useRef, useCallback } from 'react';
import { AudioRecording } from '../types';

export const useAudioRecorder = () => {
  const [isRecording, setIsRecording] = useState(false);
  const [audioURL, setAudioURL] = useState<string>('');
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);

  const startRecording = useCallback(async (): Promise<boolean> => {
    try {
      console.log('🎤 Requesting microphone access...');
      
      const stream = await navigator.mediaDevices.getUserMedia({ 
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
          sampleRate: 16000,
        } 
      });

      console.log('🎤 Got microphone stream:', stream);
      console.log('🎤 Audio tracks:', stream.getAudioTracks());
      
      // Check if audio tracks are active
      const audioTracks = stream.getAudioTracks();
      if (audioTracks.length === 0) {
        console.error('❌ No audio tracks found in stream');
        return false;
      }
      
      const audioTrack = audioTracks[0];
      console.log('🎤 Audio track settings:', audioTrack.getSettings());
      console.log('🎤 Audio track enabled:', audioTrack.enabled);

      // Check MediaRecorder support
      if (!MediaRecorder.isTypeSupported('audio/webm;codecs=opus')) {
        console.warn('⚠️ WebM/Opus not supported, trying alternatives...');
        // Fallback to basic webm
        if (!MediaRecorder.isTypeSupported('audio/webm')) {
          console.error('❌ WebM not supported at all');
          return false;
        }
      }

      const mediaRecorder = new MediaRecorder(stream, {
        mimeType: MediaRecorder.isTypeSupported('audio/webm;codecs=opus') 
          ? 'audio/webm;codecs=opus' 
          : 'audio/webm'
      });

      console.log('🎤 MediaRecorder created with mimeType:', mediaRecorder.mimeType);

      audioChunksRef.current = [];

      mediaRecorder.ondataavailable = (event) => {
        console.log('📊 Data available:', event.data.size, 'bytes');
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      mediaRecorder.onerror = (event) => {
        console.error('❌ MediaRecorder error:', event);
      };

      // Don't set onstop here - it will be set in stopRecording to avoid conflicts

      mediaRecorderRef.current = mediaRecorder;
      mediaRecorder.start(100); // Collect data every 100ms
      setIsRecording(true);
      
      console.log('🎤 Recording started successfully');
      return true;
    } catch (error) {
      console.error('❌ Error starting recording:', error);
      return false;
    }
  }, []);

  const stopRecording = useCallback((): Promise<AudioRecording | null> => {
    return new Promise((resolve) => {
      if (!mediaRecorderRef.current || !isRecording) {
        console.log('❌ Cannot stop recording - no active recorder or not recording');
        resolve(null);
        return;
      }

      console.log('🛑 Stopping recording...');

      // Set the onstop handler here to avoid conflicts
      mediaRecorderRef.current.onstop = () => {
        console.log('🛑 Recording stopped, processing chunks...');
        console.log('📊 Total chunks collected:', audioChunksRef.current.length);
        
        const totalSize = audioChunksRef.current.reduce((sum: number, chunk: Blob) => sum + chunk.size, 0);
        console.log('📊 Total audio data size:', totalSize, 'bytes');
        
        if (totalSize === 0) {
          console.error('❌ No audio data captured!');
          resolve(null);
          return;
        }

        const audioBlob = new Blob(audioChunksRef.current, { 
          type: 'audio/webm;codecs=opus' 
        });
        
        console.log('📊 Created audio blob:', audioBlob.size, 'bytes, type:', audioBlob.type);
        
        const url = URL.createObjectURL(audioBlob);
        
        const recording: AudioRecording = {
          blob: audioBlob,
          url,
          duration: 0, // We could calculate this if needed
        };

        setAudioURL(url);
        setIsRecording(false);
        
        // Stop all tracks to release the microphone
        if (mediaRecorderRef.current?.stream) {
          mediaRecorderRef.current.stream.getTracks().forEach((track: MediaStreamTrack) => {
            console.log('🛑 Stopping track:', track.kind, track.label);
            track.stop();
          });
        }
        
        console.log('✅ Recording completed successfully');
        resolve(recording);
      };

      mediaRecorderRef.current.stop();
    });
  }, [isRecording]);

  const clearRecording = useCallback(() => {
    console.log('🧹 Clearing recording...');
    if (audioURL) {
      URL.revokeObjectURL(audioURL);
      setAudioURL('');
    }
    audioChunksRef.current = [];
  }, [audioURL]);

  return {
    isRecording,
    audioURL,
    startRecording,
    stopRecording,
    clearRecording,
  };
};