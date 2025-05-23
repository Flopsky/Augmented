import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Check, X, Clock, AlertCircle } from 'lucide-react';
import { Task } from '../types';

interface TaskListProps {
  tasks: Task[];
  onCompleteTask: (id: number) => void;
  onDeleteTask: (id: number) => void;
}

export const TaskList: React.FC<TaskListProps> = ({ 
  tasks, 
  onCompleteTask, 
  onDeleteTask 
}) => {
  const activeTasks = tasks.filter(task => !task.completed);
  const completedTasks = tasks.filter(task => task.completed);

  const getPriorityColor = (priority: number) => {
    switch (priority) {
      case 5:
        return 'border-red-500 bg-red-500/10';
      case 4:
        return 'border-orange-500 bg-orange-500/10';
      case 3:
        return 'border-yellow-500 bg-yellow-500/10';
      case 2:
        return 'border-blue-500 bg-blue-500/10';
      case 1:
        return 'border-green-500 bg-green-500/10';
      default:
        return 'border-gray-500 bg-gray-500/10';
    }
  };

  const getPriorityIcon = (priority: number) => {
    if (priority >= 4) {
      return <AlertCircle className="w-4 h-4 text-red-400" />;
    }
    return <Clock className="w-4 h-4 text-gray-400" />;
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffInHours = (now.getTime() - date.getTime()) / (1000 * 60 * 60);

    if (diffInHours < 1) {
      return 'Just now';
    } else if (diffInHours < 24) {
      return `${Math.floor(diffInHours)}h ago`;
    } else {
      return date.toLocaleDateString();
    }
  };

  const TaskItem: React.FC<{ task: Task; isCompleted?: boolean }> = ({ 
    task, 
    isCompleted = false 
  }) => (
    <motion.div
      layout
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -20 }}
      className={`
        p-4 rounded-lg border-2 backdrop-blur-sm
        ${isCompleted 
          ? 'border-green-500/30 bg-green-500/5' 
          : getPriorityColor(task.priority)
        }
        transition-all duration-300 hover:shadow-lg
      `}
    >
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <div className="flex items-center space-x-2 mb-2">
            {getPriorityIcon(task.priority)}
            <span className="text-xs uppercase tracking-wide text-gray-400">
              {task.category}
            </span>
            <span className="text-xs text-gray-500">
              {formatDate(task.created_at)}
            </span>
          </div>
          
          <p className={`
            text-sm leading-relaxed
            ${isCompleted 
              ? 'text-gray-400 line-through' 
              : 'text-gray-200'
            }
          `}>
            {task.description}
          </p>
        </div>
        
        <div className="flex items-center space-x-2 ml-4">
          {!isCompleted && (
            <motion.button
              whileHover={{ scale: 1.1 }}
              whileTap={{ scale: 0.9 }}
              onClick={() => onCompleteTask(task.id)}
              className="p-2 rounded-full bg-green-500/20 hover:bg-green-500/30 
                         text-green-400 transition-colors duration-200"
              title="Mark as complete"
            >
              <Check className="w-4 h-4" />
            </motion.button>
          )}
          
          <motion.button
            whileHover={{ scale: 1.1 }}
            whileTap={{ scale: 0.9 }}
            onClick={() => onDeleteTask(task.id)}
            className="p-2 rounded-full bg-red-500/20 hover:bg-red-500/30 
                       text-red-400 transition-colors duration-200"
            title="Delete task"
          >
            <X className="w-4 h-4" />
          </motion.button>
        </div>
      </div>
    </motion.div>
  );

  return (
    <div className="w-full max-w-md space-y-6">
      {/* Active Tasks */}
      <div>
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-semibold text-gray-200">
            Active Tasks
          </h2>
          <span className="px-3 py-1 rounded-full bg-purple-500/20 text-purple-300 text-sm">
            {activeTasks.length}
          </span>
        </div>
        
        <div className="space-y-3 max-h-96 overflow-y-auto">
          <AnimatePresence>
            {activeTasks.length === 0 ? (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="text-center py-8 text-gray-500"
              >
                <Clock className="w-12 h-12 mx-auto mb-3 opacity-50" />
                <p>No active tasks</p>
                <p className="text-sm mt-1">
                  Click the voice button to add your first task
                </p>
              </motion.div>
            ) : (
              activeTasks.map((task) => (
                <TaskItem key={task.id} task={task} />
              ))
            )}
          </AnimatePresence>
        </div>
      </div>

      {/* Completed Tasks */}
      {completedTasks.length > 0 && (
        <div>
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-medium text-gray-400">
              Completed
            </h3>
            <span className="px-2 py-1 rounded-full bg-green-500/20 text-green-300 text-xs">
              {completedTasks.length}
            </span>
          </div>
          
          <div className="space-y-2 max-h-48 overflow-y-auto">
            <AnimatePresence>
              {completedTasks.slice(0, 5).map((task) => (
                <TaskItem key={task.id} task={task} isCompleted />
              ))}
            </AnimatePresence>
          </div>
          
          {completedTasks.length > 5 && (
            <p className="text-xs text-gray-500 mt-2 text-center">
              And {completedTasks.length - 5} more completed tasks
            </p>
          )}
        </div>
      )}
    </div>
  );
};