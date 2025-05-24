import React, { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { MessageCircle, CheckCircle, AlertCircle, HelpCircle } from 'lucide-react';
import { TaskAction, ActionType } from '../types';

interface ResponseDisplayProps {
  response: TaskAction | null;
  isVisible: boolean;
  onClose: () => void;
}

export const ResponseDisplay: React.FC<ResponseDisplayProps> = ({
  response,
  isVisible,
  onClose
}) => {
  const [autoCloseTimer, setAutoCloseTimer] = useState<NodeJS.Timeout | null>(null);

  useEffect(() => {
    if (isVisible && response) {
      // Auto-close after 5 seconds unless it's an unclear response
      if (response.action !== ActionType.UNCLEAR) {
        const timer = setTimeout(() => {
          onClose();
        }, 5000);
        setAutoCloseTimer(timer);
      }
    }

    return () => {
      if (autoCloseTimer) {
        clearTimeout(autoCloseTimer);
      }
    };
  }, [isVisible, response, onClose]);

  const getIcon = () => {
    if (!response) return <MessageCircle className="w-6 h-6" />;

    switch (response.action) {
      case ActionType.ADD_TASK:
        return <CheckCircle className="w-6 h-6 text-green-400" />;
      case ActionType.COMPLETE_TASK:
        return <CheckCircle className="w-6 h-6 text-blue-400" />;
      case ActionType.LIST_TASKS:
        return <MessageCircle className="w-6 h-6 text-purple-400" />;
      case ActionType.MODIFY_TASK:
        return <CheckCircle className="w-6 h-6 text-yellow-400" />;
      case ActionType.CLEAR_COMPLETED:
        return <CheckCircle className="w-6 h-6 text-orange-400" />;
      case ActionType.UNCLEAR:
        return <HelpCircle className="w-6 h-6 text-red-400" />;
      default:
        return <AlertCircle className="w-6 h-6 text-gray-400" />;
    }
  };

  const getBackgroundColor = () => {
    if (!response) return 'bg-gray-800/90';

    switch (response.action) {
      case ActionType.ADD_TASK:
        return 'bg-green-800/90';
      case ActionType.COMPLETE_TASK:
        return 'bg-blue-800/90';
      case ActionType.LIST_TASKS:
        return 'bg-purple-800/90';
      case ActionType.MODIFY_TASK:
        return 'bg-yellow-800/90';
      case ActionType.CLEAR_COMPLETED:
        return 'bg-orange-800/90';
      case ActionType.UNCLEAR:
        return 'bg-red-800/90';
      default:
        return 'bg-gray-800/90';
    }
  };

  const getBorderColor = () => {
    if (!response) return 'border-gray-600';

    switch (response.action) {
      case ActionType.ADD_TASK:
        return 'border-green-500';
      case ActionType.COMPLETE_TASK:
        return 'border-blue-500';
      case ActionType.LIST_TASKS:
        return 'border-purple-500';
      case ActionType.MODIFY_TASK:
        return 'border-yellow-500';
      case ActionType.CLEAR_COMPLETED:
        return 'border-orange-500';
      case ActionType.UNCLEAR:
        return 'border-red-500';
      default:
        return 'border-gray-600';
    }
  };

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 0.8) return 'text-green-400';
    if (confidence >= 0.6) return 'text-yellow-400';
    return 'text-red-400';
  };

  return (
    <AnimatePresence>
      {isVisible && response && (
        <motion.div
          initial={{ opacity: 0, y: 50, scale: 0.9 }}
          animate={{ opacity: 1, y: 0, scale: 1 }}
          exit={{ opacity: 0, y: 50, scale: 0.9 }}
          className="fixed bottom-6 left-1/2 transform -translate-x-1/2 z-50"
        >
          <div className={`
            ${getBackgroundColor()} ${getBorderColor()}
            backdrop-blur-sm rounded-lg border-2 p-4 shadow-2xl
            max-w-md w-full mx-4
          `}>
            <div className="flex items-start space-x-3">
              <div className="flex-shrink-0 mt-1">
                {getIcon()}
              </div>
              
              <div className="flex-1">
                <p className="text-white text-sm leading-relaxed">
                  {response.response_message}
                </p>
                
                {response.clarification_needed && (
                  <p className="text-gray-300 text-xs mt-2 italic">
                    {response.clarification_needed}
                  </p>
                )}
                
                <div className="flex items-center justify-between mt-3">
                  <div className="flex items-center space-x-2">
                    <span className="text-xs text-gray-400">
                      Action: {response.action.replace('_', ' ')}
                    </span>
                    <span className={`text-xs ${getConfidenceColor(response.confidence)}`}>
                      {Math.round(response.confidence * 100)}% confident
                    </span>
                  </div>
                  
                  {response.action !== ActionType.UNCLEAR && (
                    <button
                      onClick={onClose}
                      className="text-xs text-gray-400 hover:text-white transition-colors"
                    >
                      Dismiss
                    </button>
                  )}
                </div>
              </div>
            </div>
            
            {/* Progress bar for auto-close */}
            {response.action !== ActionType.UNCLEAR && (
              <motion.div
                className="absolute bottom-0 left-0 h-1 bg-white/30 rounded-b-lg"
                initial={{ width: '100%' }}
                animate={{ width: '0%' }}
                transition={{ duration: 5, ease: 'linear' }}
              />
            )}
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  );
};