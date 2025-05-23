export interface Task {
  id: number;
  description: string;
  completed: boolean;
  priority: number;
  category: string;
  created_at: string;
  updated_at?: string;
  remind_at?: string;
  recurring: boolean;
}

export interface TaskCreate {
  description: string;
  priority?: number;
  category?: string;
  remind_at?: string;
  recurring?: boolean;
}

export interface TaskUpdate {
  description?: string;
  completed?: boolean;
  priority?: number;
  category?: string;
  remind_at?: string;
  recurring?: boolean;
}

export enum ActionType {
  ADD_TASK = "add_task",
  COMPLETE_TASK = "complete_task",
  LIST_TASKS = "list_tasks",
  MODIFY_TASK = "modify_task",
  CLEAR_COMPLETED = "clear_completed",
  UPDATE_REMINDER = "update_reminder",
  UNCLEAR = "unclear"
}

export interface TaskAction {
  action: ActionType;
  task_description?: string;
  task_identifier?: string;
  new_description?: string;
  reminder_interval?: number;
  priority_level?: number;
  suggested_category?: string;
  confidence: number;
  response_message: string;
  clarification_needed?: string;
}

export interface VoiceCommandResponse {
  action: TaskAction;
  success: boolean;
  message: string;
}

export enum AppState {
  IDLE = "idle",
  LISTENING = "listening",
  PROCESSING = "processing",
  SPEAKING = "speaking",
  ERROR = "error"
}

export interface AudioRecording {
  blob: Blob;
  url: string;
  duration: number;
}

export interface WebSocketMessage {
  type: string;
  data?: any;
  tasks?: Task[];
}