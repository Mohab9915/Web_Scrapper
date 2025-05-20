/**
 * WebSocket connection manager for real-time updates
 */
import { API_URL } from './api';

// Convert HTTP URL to WebSocket URL
const WS_URL = API_URL.replace(/^http/, 'ws');

export interface ProgressUpdate {
  status: 'processing' | 'completed' | 'error';
  message: string;
  current_chunk: number;
  total_chunks: number;
  percent_complete: number;
  performance_metrics?: {
    chunks_per_second?: number;
    processing_time?: number;
  };
}

export interface WebSocketMessage {
  type: 'progress_update' | 'error' | 'connected';
  session_id?: string;
  project_id?: string;
  data?: ProgressUpdate;
  error?: string;
}

type MessageCallback = (message: WebSocketMessage) => void;
type ErrorCallback = (error: Event) => void;
type ConnectCallback = () => void;

class WebSocketManager {
  private socket: WebSocket | null = null;
  private projectId: string | null = null;
  private messageCallbacks: MessageCallback[] = [];
  private errorCallbacks: ErrorCallback[] = [];
  private connectCallbacks: ConnectCallback[] = [];
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectTimeout: NodeJS.Timeout | null = null;

  /**
   * Connect to the WebSocket server for a specific project
   */
  connect(projectId: string): void {
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
        const message = JSON.parse(event.data) as WebSocketMessage;
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
  disconnect(): void {
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
  private attemptReconnect(): void {
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
  onMessage(callback: MessageCallback): () => void {
    this.messageCallbacks.push(callback);
    return () => {
      this.messageCallbacks = this.messageCallbacks.filter(cb => cb !== callback);
    };
  }

  /**
   * Register a callback for WebSocket errors
   */
  onError(callback: ErrorCallback): () => void {
    this.errorCallbacks.push(callback);
    return () => {
      this.errorCallbacks = this.errorCallbacks.filter(cb => cb !== callback);
    };
  }

  /**
   * Register a callback for WebSocket connection
   */
  onConnect(callback: ConnectCallback): () => void {
    this.connectCallbacks.push(callback);
    return () => {
      this.connectCallbacks = this.connectCallbacks.filter(cb => cb !== callback);
    };
  }

  /**
   * Check if WebSocket is connected
   */
  isConnected(): boolean {
    return this.socket !== null && this.socket.readyState === WebSocket.OPEN;
  }
}

// Export a singleton instance
export const webSocketManager = new WebSocketManager();
