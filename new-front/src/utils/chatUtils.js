/**
 * Utility functions for chat functionality
 */
import { getChatMessages } from '../lib/api';

/**
 * Load chat messages for a project and conversation
 * @param {string} projectId - The project ID
 * @param {string} conversationId - The conversation ID (optional)
 * @param {function} setMessages - State setter function for messages
 * @param {function} setError - State setter function for errors (optional)
 */
export const loadChatMessages = async (projectId, conversationId, setMessages, setError) => {
  if (!projectId) {
    setMessages([]);
    return;
  }

  try {
    console.log('Loading messages for project:', projectId, 'conversation:', conversationId || 'latest');
    const messages = await getChatMessages(projectId, conversationId);
    console.log('Retrieved messages:', messages);
    setMessages(messages || []);
  } catch (error) {
    console.error('Error loading chat messages:', error);
    setMessages([]);
    if (setError) {
      setError('Failed to load chat messages');
    }
  }
};

/**
 * Format a chat message for display
 * @param {Object} message - The chat message object
 * @returns {Object} - Formatted message
 */
export const formatChatMessage = (message) => {
  return {
    ...message,
    formattedTime: new Date(message.timestamp).toLocaleTimeString(),
    formattedDate: new Date(message.timestamp).toLocaleDateString()
  };
};
