/**
 * Centralized API configuration for production deployments.
 * 
 * This file manages the backend API base URL and ensures
 * all API requests use environment variables instead of hardcoded URLs.
 * 
 * Environment Variables:
 * - NEXT_PUBLIC_BACKEND_API_URL: Backend API base URL (required)
 * 
 * Example Values:
 * - Local Development: http://localhost:8000
 * - Production: https://laibatheuser-h2-p3-todochatbot.hf.space
 */

// Get backend URL from environment variable
const getBackendUrl = (): string => {
  const url = process.env.NEXT_PUBLIC_BACKEND_API_URL;
  
  if (!url || url.trim() === '') {
    // Provide helpful error in development
    if (process.env.NODE_ENV === 'development') {
      console.warn(
        '⚠️ NEXT_PUBLIC_BACKEND_API_URL is not set. ' +
        'Please create a .env.local file with:\n' +
        'NEXT_PUBLIC_BACKEND_API_URL=http://localhost:8000'
      );
      // Fallback for local development ONLY
      return 'http://localhost:8000';
    }
    
    // In production, throw error to prevent silent failures
    throw new Error(
      'NEXT_PUBLIC_BACKEND_API_URL environment variable is not set. ' +
      'Please configure it in Vercel dashboard.'
    );
  }
  
  // Remove trailing slash if present
  return url.replace(/\/$/, '');
};

// Export the configured base URL
export const API_BASE_URL = getBackendUrl();

// API endpoints configuration
export const API_ENDPOINTS = {
  // Authentication
  LOGIN: '/api/auth/login',
  REGISTER: '/api/auth/register',
  LOGOUT: '/api/auth/logout',
  ME: '/api/auth/me',
  
  // Tasks
  TASKS: '/api/tasks',
  
  // Chat
  CHAT: (userId: string) => `/api/v1/${userId}/chat`,
  
  // Health
  HEALTH: '/api/health',
} as const;

// Helper function to build full URL
export const buildUrl = (endpoint: string): string => {
  return `${API_BASE_URL}${endpoint}`;
};

// Type-safe endpoint builder for dynamic routes
export const buildChatUrl = (userId: string): string => {
  return buildUrl(API_ENDPOINTS.CHAT(userId));
};

export default {
  API_BASE_URL,
  API_ENDPOINTS,
  buildUrl,
  buildChatUrl,
};
