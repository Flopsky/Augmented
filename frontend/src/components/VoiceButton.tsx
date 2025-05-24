import React from 'react';
import { motion } from 'framer-motion';
import { Mic, MicOff, Loader2 } from 'lucide-react';
import { AppState } from '../types';

interface VoiceButtonProps {
  state: AppState;
  onClick: () => void;
  disabled?: boolean;
}

export const VoiceButton: React.FC<VoiceButtonProps> = ({ 
  state, 
  onClick, 
  disabled = false 
}) => {
  const getButtonContent = () => {
    switch (state) {
      case AppState.LISTENING:
        return <Mic className="w-12 h-12 text-white" />;
      case AppState.PROCESSING:
        return <Loader2 className="w-12 h-12 text-white animate-spin" />;
      case AppState.SPEAKING:
        return <Mic className="w-12 h-12 text-white" />;
      case AppState.ERROR:
        return <MicOff className="w-12 h-12 text-red-300" />;
      default:
        return <Mic className="w-12 h-12 text-white" />;
    }
  };

  const getButtonVariants = () => {
    const baseVariants = {
      idle: {
        scale: 1,
        boxShadow: '0 0 0 0 rgba(168, 85, 247, 0.4)',
      },
      listening: {
        scale: 1.05,
        boxShadow: [
          '0 0 0 0 rgba(168, 85, 247, 0.4)',
          '0 0 0 20px rgba(168, 85, 247, 0)',
          '0 0 0 0 rgba(168, 85, 247, 0)',
        ],
        transition: {
          boxShadow: {
            duration: 2,
            repeat: Infinity,
            ease: 'easeInOut',
          },
          scale: {
            duration: 0.3,
          },
        },
      },
      processing: {
        scale: 0.95,
        boxShadow: '0 0 0 0 rgba(59, 130, 246, 0.4)',
      },
      speaking: {
        scale: [1, 1.1, 1],
        boxShadow: [
          '0 0 0 0 rgba(34, 197, 94, 0.4)',
          '0 0 0 15px rgba(34, 197, 94, 0)',
          '0 0 0 0 rgba(34, 197, 94, 0.4)',
        ],
        transition: {
          scale: {
            duration: 1.5,
            repeat: Infinity,
            ease: 'easeInOut',
          },
          boxShadow: {
            duration: 1.5,
            repeat: Infinity,
            ease: 'easeInOut',
          },
        },
      },
      error: {
        scale: 1,
        boxShadow: '0 0 0 0 rgba(239, 68, 68, 0.4)',
        backgroundColor: 'rgba(239, 68, 68, 0.2)',
      },
    };

    return baseVariants;
  };

  const getGradientClass = () => {
    switch (state) {
      case AppState.LISTENING:
        return 'bg-gradient-to-br from-purple-500 to-purple-700';
      case AppState.PROCESSING:
        return 'bg-gradient-to-br from-blue-500 to-blue-700';
      case AppState.SPEAKING:
        return 'bg-gradient-to-br from-green-500 to-green-700';
      case AppState.ERROR:
        return 'bg-gradient-to-br from-red-500 to-red-700';
      default:
        return 'bg-gradient-to-br from-purple-600 to-blue-600';
    }
  };

  return (
    <div className="flex flex-col items-center space-y-4">
      <motion.button
        className={`
          w-36 h-36 rounded-full flex items-center justify-center
          ${getGradientClass()}
          shadow-2xl border-4 border-white/20
          ${disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer hover:shadow-3xl'}
          transition-all duration-300
        `}
        variants={getButtonVariants()}
        animate={state}
        onClick={onClick}
        disabled={disabled}
        whileHover={!disabled ? { scale: 1.05 } : {}}
        whileTap={!disabled ? { scale: 0.95 } : {}}
      >
        {getButtonContent()}
      </motion.button>
      
      <motion.div
        className="text-center"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.2 }}
      >
        <p className="text-lg font-medium text-gray-300">
          {state === AppState.IDLE && 'Click to speak'}
          {state === AppState.LISTENING && 'Listening...'}
          {state === AppState.PROCESSING && 'Processing...'}
          {state === AppState.SPEAKING && 'Speaking...'}
          {state === AppState.ERROR && 'Error occurred'}
        </p>
        
        {state === AppState.IDLE && (
          <p className="text-sm text-gray-500 mt-1">
            Say "Add buy milk" or "I finished the groceries"
          </p>
        )}
      </motion.div>
    </div>
  );
};