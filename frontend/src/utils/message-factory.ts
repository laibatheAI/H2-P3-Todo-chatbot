import { Message } from '@/types/chat';

/**
 * Creates a typed user message with guaranteed type safety
 */
export function createUserMessage(content: string): Message {
  return {
    id: crypto.randomUUID(),
    role: 'user' as const,
    content,
    timestamp: Date.now(),
  };
}

/**
 * Creates a typed assistant message with guaranteed type safety
 */
export function createAssistantMessage(content: string): Message {
  return {
    id: crypto.randomUUID(),
    role: 'assistant' as const,
    content,
    timestamp: Date.now(),
  };
}

/**
 * Creates an error message (displayed as assistant message)
 * Error messages use assistant role for UI consistency
 */
export function createErrorMessage(errorText: string): Message {
  return {
    id: crypto.randomUUID(),
    role: 'assistant' as const,
    content: `Error: ${errorText}. Please try again.`,
    timestamp: Date.now(),
  };
}

/**
 * Generic message creator with explicit role typing
 * Use this when role is determined dynamically
 */
export function createMessage(
  role: 'user' | 'assistant',
  content: string
): Message {
  return {
    id: crypto.randomUUID(),
    role,
    content,
    timestamp: Date.now(),
  };
}
