import React from 'react';
import { motion } from 'framer-motion';
import { Wifi, WifiOff, Volume2, VolumeX, Mic, MicOff } from 'lucide-react';

interface StatusIndicatorProps {
  isConnected: boolean;
  hasAudioPermission: boolean;
  isTTSEnabled: boolean;
  lastUpdate?: string;
}

export const StatusIndicator: React.FC<StatusIndicatorProps> = ({
  isConnected,
  hasAudioPermission,
  isTTSEnabled,
  lastUpdate
}) => {
  return (
    <motion.div
      initial={{ opacity: 0, y: -20 }}
      animate={{ opacity: 1, y: 0 }}
      className="fixed top-4 right-4 bg-gray-800/80 backdrop-blur-sm rounded-lg p-3 border border-gray-700"
    >
      <div className="flex items-center space-x-3">
        {/* WebSocket Connection */}
        <div className="flex items-center space-x-1">
          {isConnected ? (
            <Wifi className="w-4 h-4 text-green-400" />
          ) : (
            <WifiOff className="w-4 h-4 text-red-400" />
          )}
          <span className="text-xs text-gray-400">
            {isConnected ? 'Connected' : 'Disconnected'}
          </span>
        </div>

        {/* Audio Permission */}
        <div className="flex items-center space-x-1">
          {hasAudioPermission ? (
            <Mic className="w-4 h-4 text-green-400" />
          ) : (
            <MicOff className="w-4 h-4 text-red-400" />
          )}
          <span className="text-xs text-gray-400">
            {hasAudioPermission ? 'Mic OK' : 'No Mic'}
          </span>
        </div>

        {/* TTS Status */}
        <div className="flex items-center space-x-1">
          {isTTSEnabled ? (
            <Volume2 className="w-4 h-4 text-green-400" />
          ) : (
            <VolumeX className="w-4 h-4 text-yellow-400" />
          )}
          <span className="text-xs text-gray-400">
            {isTTSEnabled ? 'TTS' : 'No TTS'}
          </span>
        </div>
      </div>

      {lastUpdate && (
        <div className="mt-2 pt-2 border-t border-gray-700">
          <p className="text-xs text-gray-500">
            Last update: {new Date(lastUpdate).toLocaleTimeString()}
          </p>
        </div>
      )}
    </motion.div>
  );
};