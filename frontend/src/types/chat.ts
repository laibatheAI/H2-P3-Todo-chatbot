// Strictly typed message types for chat interface

export type MessageRole = 'user' | 'assistant';

export interface Message {
  id: string;
  role: MessageRole;
  content: string;
  timestamp?: number;
}

export interface ChatError {
  id: string;
  type: 'error';
  message: string;
  timestamp: number;
}

// Type guard for message validation
export function isMessage(obj: unknown): obj is Message {
  return (
    typeof obj === 'object' &&
    obj !== null &&
    'id' in obj &&
    'role' in obj &&
    'content' in obj &&
    typeof obj.id === 'string' &&
    (obj.role === 'user' || obj.role === 'assistant') &&
    typeof obj.content === 'string'
  );
}
