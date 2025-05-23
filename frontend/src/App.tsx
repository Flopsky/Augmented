import React, { useState, useEffect, useCallback } from 'react';
import { QueryClient, QueryClientProvider, useQuery, useQueryClient } from '@tanstack/react-query';
import { motion } from 'framer-motion';
import { VoiceButton } from './components/VoiceButton';
import { TaskList } from './components/TaskList';
import { StatusIndicator } from './components/StatusIndicator';
import { ResponseDisplay } from './components/ResponseDisplay';
import { useAudioRecorder } from './hooks/useAudioRecorder';
import { useWebSocket } from './hooks/useWebSocket';
import { taskApi, voiceApi, blobToBase64 } from './utils/api';
import { AppState, Task, TaskAction } from './types';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
    },
  },
});

const AppContent: React.FC = () => {
  const [appState, setAppState] = useState<AppState>(AppState.IDLE);
  const [hasAudioPermission, setHasAudioPermission] = useState(false);
  const [lastResponse, setLastResponse] = useState<TaskAction | null>(null);
  const [showResponse, setShowResponse] = useState(false);
  const [lastUpdate, setLastUpdate] = useState<string>('');

  const queryClient = useQueryClient();
  const { isConnected, tasks: wsTasks } = useWebSocket();
  const {
    isRecording,
    startRecording,
    stopRecording,
    clearRecording,
  } = useAudioRecorder();

  // Fetch tasks
  const { data: tasks = [], refetch: refetchTasks } = useQuery({
    queryKey: ['tasks'],
    queryFn: () => taskApi.getTasks(false),
    refetchInterval: 30000, // Refetch every 30 seconds
  });

  // Check audio permission on mount
  useEffect(() => {
    const checkAudioPermission = async () => {
      try {
        await navigator.mediaDevices.getUserMedia({ audio: true });
        setHasAudioPermission(true);
      } catch (error) {
        console.error('Audio permission denied:', error);
        setHasAudioPermission(false);
      }
    };

    checkAudioPermission();
  }, []);

  // Update tasks when WebSocket receives updates
  useEffect(() => {
    if (wsTasks.length > 0) {
      queryClient.setQueryData(['tasks'], wsTasks);
      setLastUpdate(new Date().toISOString());
    }
  }, [wsTasks, queryClient]);

  const handleVoiceButtonClick = useCallback(async () => {
    if (!hasAudioPermission) {
      alert('Microphone permission is required for voice commands');
      return;
    }

    if (appState === AppState.LISTENING) {
      // Stop recording and process
      setAppState(AppState.PROCESSING);
      
      try {
        const recording = await stopRecording();
        if (recording) {
          const audioBase64 = await blobToBase64(recording.blob);
          const response = await voiceApi.processVoiceCommand(audioBase64);
          
          setLastResponse(response.action);
          setShowResponse(true);
          setAppState(AppState.IDLE);
          
          // Refetch tasks to get updated list
          await refetchTasks();
          setLastUpdate(new Date().toISOString());
        }
      } catch (error) {
        console.error('Error processing voice command:', error);
        setAppState(AppState.ERROR);
        setTimeout(() => setAppState(AppState.IDLE), 2000);
      } finally {
        clearRecording();
      }
    } else if (appState === AppState.IDLE) {
      // Start recording
      const success = await startRecording();
      if (success) {
        setAppState(AppState.LISTENING);
      } else {
        setAppState(AppState.ERROR);
        setTimeout(() => setAppState(AppState.IDLE), 2000);
      }
    }
  }, [appState, hasAudioPermission, startRecording, stopRecording, clearRecording, refetchTasks]);

  const handleCompleteTask = useCallback(async (id: number) => {
    try {
      await taskApi.completeTask(id);
      await refetchTasks();
      setLastUpdate(new Date().toISOString());
    } catch (error) {
      console.error('Error completing task:', error);
    }
  }, [refetchTasks]);

  const handleDeleteTask = useCallback(async (id: number) => {
    try {
      await taskApi.deleteTask(id);
      await refetchTasks();
      setLastUpdate(new Date().toISOString());
    } catch (error) {
      console.error('Error deleting task:', error);
    }
  }, [refetchTasks]);

  const handleCloseResponse = useCallback(() => {
    setShowResponse(false);
    setLastResponse(null);
  }, []);

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-purple-900 to-blue-900 relative overflow-hidden">
      {/* Background decoration */}
      <div className="absolute inset-0 overflow-hidden">
        <div className="absolute -top-40 -right-40 w-80 h-80 bg-purple-500 rounded-full mix-blend-multiply filter blur-xl opacity-20 animate-blob"></div>
        <div className="absolute -bottom-40 -left-40 w-80 h-80 bg-blue-500 rounded-full mix-blend-multiply filter blur-xl opacity-20 animate-blob animation-delay-2000"></div>
        <div className="absolute top-40 left-40 w-80 h-80 bg-pink-500 rounded-full mix-blend-multiply filter blur-xl opacity-20 animate-blob animation-delay-4000"></div>
      </div>

      {/* Status Indicator */}
      <StatusIndicator
        isConnected={isConnected}
        hasAudioPermission={hasAudioPermission}
        isTTSEnabled={false} // TTS is not implemented yet
        lastUpdate={lastUpdate}
      />

      {/* Main Content */}
      <div className="relative z-10 flex items-center justify-center min-h-screen p-8">
        <div className="flex items-start space-x-12 w-full max-w-6xl">
          {/* Voice Button - Center */}
          <div className="flex-1 flex justify-center">
            <motion.div
              initial={{ opacity: 0, scale: 0.8 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ duration: 0.5 }}
            >
              <VoiceButton
                state={appState}
                onClick={handleVoiceButtonClick}
                disabled={!hasAudioPermission}
              />
            </motion.div>
          </div>

          {/* Task List - Right */}
          <motion.div
            initial={{ opacity: 0, x: 50 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.5, delay: 0.2 }}
            className="flex-1"
          >
            <TaskList
              tasks={tasks}
              onCompleteTask={handleCompleteTask}
              onDeleteTask={handleDeleteTask}
            />
          </motion.div>
        </div>
      </div>

      {/* Response Display */}
      <ResponseDisplay
        response={lastResponse}
        isVisible={showResponse}
        onClose={handleCloseResponse}
      />

      {/* App Title */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, delay: 0.3 }}
        className="absolute top-8 left-8"
      >
        <h1 className="text-3xl font-bold text-white">
          Task Reminder
        </h1>
        <p className="text-gray-400 text-sm mt-1">
          Your voice-powered task assistant
        </p>
      </motion.div>
    </div>
  );
};

const App: React.FC = () => {
  return (
    <QueryClientProvider client={queryClient}>
      <AppContent />
    </QueryClientProvider>
  );
};

export default App;