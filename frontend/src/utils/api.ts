import axios from 'axios';
import { Task, TaskCreate, TaskUpdate, VoiceCommandResponse } from '../types';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Task API
export const taskApi = {
  getTasks: async (includeCompleted = false): Promise<Task[]> => {
    const response = await api.get(`/api/tasks?include_completed=${includeCompleted}`);
    return response.data;
  },

  getTask: async (id: number): Promise<Task> => {
    const response = await api.get(`/api/tasks/${id}`);
    return response.data;
  },

  createTask: async (task: TaskCreate): Promise<Task> => {
    const response = await api.post('/api/tasks', task);
    return response.data;
  },

  updateTask: async (id: number, task: TaskUpdate): Promise<Task> => {
    const response = await api.put(`/api/tasks/${id}`, task);
    return response.data;
  },

  deleteTask: async (id: number): Promise<void> => {
    await api.delete(`/api/tasks/${id}`);
  },

  completeTask: async (id: number): Promise<Task> => {
    const response = await api.post(`/api/tasks/${id}/complete`);
    return response.data;
  },

  clearCompleted: async (): Promise<{ message: string }> => {
    const response = await api.delete('/api/tasks/completed');
    return response.data;
  },
};

// Voice API
export const voiceApi = {
  processVoiceCommand: async (audioData: string): Promise<VoiceCommandResponse> => {
    const response = await api.post('/api/voice/process-command', {
      audio_data: audioData,
    });
    return response.data;
  },

  speechToText: async (audioData: string): Promise<{ text: string; success: boolean }> => {
    const response = await api.post('/api/voice/speech-to-text', {
      audio_data: audioData,
    });
    return response.data;
  },

  textToSpeech: async (text: string): Promise<{ audio_data: string; success: boolean }> => {
    const response = await api.post('/api/voice/text-to-speech', {
      text,
    });
    return response.data;
  },

  processTextCommand: async (text: string): Promise<VoiceCommandResponse> => {
    const response = await api.post('/api/voice/process-text', null, {
      params: { text },
    });
    return response.data;
  },
};

// TTS API (Enhanced voice features)
export const ttsApi = {
  // Get TTS audio directly as blob for immediate playback
  getTTSAudio: async (text: string, voice: string = 'af_bella', speed: number = 1.0): Promise<Blob | null> => {
    try {
      const response = await api.get(`/api/voice/tts/${encodeURIComponent(text)}`, {
        params: { voice, speed },
        responseType: 'blob',
      });
      return response.data;
    } catch (error) {
      console.error('Error getting TTS audio:', error);
      return null;
    }
  },

  // Get TTS audio as base64 (JSON response)
  getTTSBase64: async (text: string): Promise<{ audio_data: string; success: boolean }> => {
    const response = await api.post('/api/voice/text-to-speech', { text });
    return response.data;
  },

  // Get available voices
  getAvailableVoices: async (): Promise<{
    voices: string[];
    default_voice: string;
    source: string;
    tts_available: boolean;
  }> => {
    const response = await api.get('/api/voice/voices');
    return response.data;
  },

  // Check TTS service status
  getTTSStatus: async (): Promise<{
    available: boolean;
    service: string;
    base_url?: string;
    default_voice?: string;
    cache_enabled?: boolean;
    error?: string;
  }> => {
    const response = await api.get('/api/voice/tts/status');
    return response.data;
  },

  // Play TTS audio directly (convenience function)
  playTTS: async (text: string, voice: string = 'af_bella', speed: number = 1.0): Promise<boolean> => {
    try {
      const audioBlob = await ttsApi.getTTSAudio(text, voice, speed);
      if (audioBlob) {
        const audio = new Audio(URL.createObjectURL(audioBlob));
        await audio.play();
        return true;
      }
      return false;
    } catch (error) {
      console.error('Error playing TTS:', error);
      return false;
    }
  },
};

// Audio utility functions
export const audioUtils = {
  // Create audio element from base64 data
  createAudioFromBase64: (base64: string, mimeType: string = 'audio/mpeg'): HTMLAudioElement => {
    const blob = base64ToBlob(base64, mimeType);
    const url = URL.createObjectURL(blob);
    const audio = new Audio(url);
    
    // Clean up URL when audio ends
    audio.addEventListener('ended', () => {
      URL.revokeObjectURL(url);
    });
    
    return audio;
  },

  // Play audio from base64 data
  playBase64Audio: async (base64: string, mimeType: string = 'audio/mpeg'): Promise<boolean> => {
    try {
      const audio = audioUtils.createAudioFromBase64(base64, mimeType);
      await audio.play();
      return true;
    } catch (error) {
      console.error('Error playing audio:', error);
      return false;
    }
  },

  // Create download link for audio
  downloadAudio: (audioData: string | Blob, filename: string): void => {
    let blob: Blob;
    
    if (typeof audioData === 'string') {
      blob = base64ToBlob(audioData, 'audio/mpeg');
    } else {
      blob = audioData;
    }
    
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    a.click();
    URL.revokeObjectURL(url);
  },
};

// Utility functions
export const blobToBase64 = (blob: Blob): Promise<string> => {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => {
      const result = reader.result as string;
      // Remove the data URL prefix (e.g., "data:audio/wav;base64,")
      const base64 = result.split(',')[1];
      resolve(base64);
    };
    reader.onerror = reject;
    reader.readAsDataURL(blob);
  });
};

export const base64ToBlob = (base64: string, mimeType: string): Blob => {
  const byteCharacters = atob(base64);
  const byteNumbers = new Array(byteCharacters.length);
  for (let i = 0; i < byteCharacters.length; i++) {
    byteNumbers[i] = byteCharacters.charCodeAt(i);
  }
  const byteArray = new Uint8Array(byteNumbers);
  return new Blob([byteArray], { type: mimeType });
};

export default api;