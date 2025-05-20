/**
 * WebSocket connection manager for real-time updates
 */
import { API_URL } from './api';

// Convert HTTP URL to WebSocket URL
const WS_URL = API_URL.replace(/^http/, 'ws');

class WebSocketManager {
  constructor() {
    this.socket = null;
    this.projectId = null;
    this.messageCallbacks = [];
    this.errorCallbacks = [];
    this.connectCallbacks = [];
    this.reconnectAttempts = 0;
    this.maxReconnectAttempts = 5;
    this.reconnectTimeout = null;
  }

  /**
   * Connect to the WebSocket server for a specific project
   */
  connect(projectId) {
    if (this.socket && this.socket.readyState === WebSocket.OPEN && this.projectId === projectId) {
      console.log('WebSocket already connected for this project');
      return;
    }

    // Close existing connection if any
    this.disconnect();

    this.projectId = projectId;
    this.socket = new WebSocket(`${WS_URL}/ws/projects/${projectId}`);

    this.socket.onopen = () => {
      console.log(`WebSocket connected for project ${projectId}`);
      this.reconnectAttempts = 0;
      this.connectCallbacks.forEach(callback => callback());
    };

    this.socket.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data);
        this.messageCallbacks.forEach(callback => callback(message));
      } catch (error) {
        console.error('Error parsing WebSocket message:', error);
      }
    };

    this.socket.onerror = (error) => {
      console.error('WebSocket error:', error);
      this.errorCallbacks.forEach(callback => callback(error));
    };

    this.socket.onclose = () => {
      console.log('WebSocket connection closed');
      
      // Attempt to reconnect if not manually disconnected
      if (this.projectId) {
        this.attemptReconnect();
      }
    };
  }

  /**
   * Disconnect from the WebSocket server
   */
  disconnect() {
    if (this.reconnectTimeout) {
      clearTimeout(this.reconnectTimeout);
      this.reconnectTimeout = null;
    }

    if (this.socket) {
      this.socket.close();
      this.socket = null;
    }
    
    this.projectId = null;
    this.reconnectAttempts = 0;
  }

  /**
   * Attempt to reconnect to the WebSocket server
   */
  attemptReconnect() {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.log('Maximum reconnect attempts reached');
      return;
    }

    const delay = Math.min(1000 * Math.pow(2, this.reconnectAttempts), 30000);
    console.log(`Attempting to reconnect in ${delay}ms (attempt ${this.reconnectAttempts + 1}/${this.maxReconnectAttempts})`);

    this.reconnectTimeout = setTimeout(() => {
      if (this.projectId) {
        this.reconnectAttempts++;
        this.connect(this.projectId);
      }
    }, delay);
  }

  /**
   * Register a callback for WebSocket messages
   */
  onMessage(callback) {
    this.messageCallbacks.push(callback);
    return () => {
      this.messageCallbacks = this.messageCallbacks.filter(cb => cb !== callback);
    };
  }

  /**
   * Register a callback for WebSocket errors
   */
  onError(callback) {
    this.errorCallbacks.push(callback);
    return () => {
      this.errorCallbacks = this.errorCallbacks.filter(cb => cb !== callback);
    };
  }

  /**
   * Register a callback for WebSocket connection
   */
  onConnect(callback) {
    this.connectCallbacks.push(callback);
    return () => {
      this.connectCallbacks = this.connectCallbacks.filter(cb => cb !== callback);
    };
  }

  /**
   * Check if WebSocket is connected
   */
  isConnected() {
    return this.socket !== null && this.socket.readyState === WebSocket.OPEN;
  }
}

// Export a singleton instance
export const webSocketManager = new WebSocketManager();
