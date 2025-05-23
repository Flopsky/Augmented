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