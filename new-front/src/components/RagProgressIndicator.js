import React, { useEffect, useState } from 'react';
import { API_URL } from '../lib/api';

function RagProgressIndicator({ projectId, sessionId, onComplete, className = '' }) {
  const [progress, setProgress] = useState({
    status: 'idle',
    message: 'Waiting to start RAG ingestion...',
    current_chunk: 0,
    total_chunks: 0,
    percent_complete: 0
  });
  const [socket, setSocket] = useState(null);
  const [connectionError, setConnectionError] = useState(null);

  useEffect(() => {
    // Create WebSocket connection
    // Convert HTTP URL to WebSocket URL and use port 8000 for backend
    const wsBaseUrl = API_URL.replace(/^http/, 'ws');
    const wsUrl = `${wsBaseUrl}/ws/projects/${projectId}`;
    const ws = new WebSocket(wsUrl);

    // Connection opened
    ws.addEventListener('open', () => {
      console.log('WebSocket connection established');
      setConnectionError(null);
    });

    // Listen for messages
    ws.addEventListener('message', (event) => {
      try {
        const data = JSON.parse(event.data);

        // Handle progress updates
        if (data.type === 'progress_update' && data.session_id === sessionId) {
          // Extract performance metrics from the message if available
          const updatedData = { ...data.data };

          // Parse performance metrics from the message
          if (data.data.message && !data.data.performance_metrics) {
            const chunksPerSecondMatch = data.data.message.match(/\(([0-9.]+) chunks\/sec\)/);
            const processingTimeMatch = data.data.message.match(/in ([0-9.]+) seconds/);

            if (chunksPerSecondMatch || processingTimeMatch) {
              updatedData.performance_metrics = {
                ...(chunksPerSecondMatch ? { chunks_per_second: parseFloat(chunksPerSecondMatch[1]) } : {}),
                ...(processingTimeMatch ? { processing_time: parseFloat(processingTimeMatch[1]) } : {})
              };
            }
          }

          setProgress(updatedData);

          // Call onComplete callback when processing is completed
          if (data.data.status === 'completed' && onComplete) {
            onComplete();
          }
        }
      } catch (error) {
        console.error('Error parsing WebSocket message:', error);
      }
    });

    // Handle errors
    ws.addEventListener('error', (error) => {
      console.error('WebSocket error:', error);
      setConnectionError('WebSocket connection failed');
      setProgress({
        status: 'error',
        message: 'Connection error. Please try again.',
        error: 'WebSocket connection failed'
      });
    });

    // Handle connection close
    ws.addEventListener('close', () => {
      console.log('WebSocket connection closed');
      // Only set connection error if it was not an intentional close
      if (!connectionError) {
        setConnectionError('WebSocket connection closed');
      }
    });

    // Store socket in state
    setSocket(ws);

    // Clean up on unmount
    return () => {
      if (ws.readyState === WebSocket.OPEN) {
        ws.close();
      }
    };
  }, [projectId, sessionId, onComplete, connectionError]);

  // Render different UI based on status
  const renderStatusIcon = () => {
    switch (progress.status) {
      case 'processing':
        return <div className="animate-spin">⟳</div>;
      case 'completed':
        return <div className="text-green-500">✓</div>;
      case 'error':
        return <div className="text-red-500">⚠</div>;
      default:
        return null;
    }
  };

  const getStatusBadge = () => {
    switch (progress.status) {
      case 'idle':
        return <span className="badge badge-outline">Idle</span>;
      case 'processing':
        return <span className="badge badge-secondary">Processing</span>;
      case 'completed':
        return <span className="badge badge-success">Completed</span>;
      case 'error':
        return <span className="badge badge-error">Error</span>;
      default:
        return null;
    }
  };

  // Render performance metrics if available
  const renderPerformanceMetrics = () => {
    if (!progress.performance_metrics) return null;

    const { chunks_per_second, processing_time, batch_size, total_batches } = progress.performance_metrics;

    return (
      <div className="flex flex-wrap gap-2 mt-2">
        {chunks_per_second !== undefined && (
          <span className="badge badge-outline text-xs">
            {chunks_per_second.toFixed(2)} chunks/sec
          </span>
        )}
        {processing_time !== undefined && (
          <span className="badge badge-outline text-xs">
            {processing_time.toFixed(2)}s processing time
          </span>
        )}
        {batch_size !== undefined && (
          <span className="badge badge-outline text-xs">
            Batch size: {batch_size}
          </span>
        )}
        {total_batches !== undefined && (
          <span className="badge badge-outline text-xs">
            {total_batches} batches
          </span>
        )}
      </div>
    );
  };

  return (
    <div className={`card ${className || "w-full"}`}>
      <div className="card-header pb-2">
        <div className="flex items-center justify-between">
          <h3 className="card-title text-lg">RAG Ingestion Progress</h3>
          {getStatusBadge()}
        </div>
        {progress.message && (
          <p className="card-description">{progress.message}</p>
        )}
      </div>
      <div className="card-content">
        <div className="space-y-4">
          <div className="flex items-center gap-2">
            {renderStatusIcon()}
            <p className="text-sm font-medium">
              {progress.status === 'processing' ? 'Processing in progress...' :
               progress.status === 'completed' ? 'Processing complete!' :
               progress.status === 'error' ? 'Processing failed' : 'Waiting to start...'}
            </p>
          </div>

          {(progress.status === 'processing' || progress.status === 'completed') && progress.total_chunks && progress.total_chunks > 0 && (
            <>
              <div className="progress-bar">
                <div 
                  className="progress-bar-fill" 
                  style={{
                    width: `${progress.status === 'completed' ? 100 : (progress.percent_complete || 0)}%`,
                    backgroundColor: progress.status === 'completed' ? 'green' : 'blue'
                  }}
                />
              </div>
              <div className="flex justify-between items-center">
                <p className="text-xs text-muted">
                  {progress.current_chunk} of {progress.total_chunks} chunks processed
                  {progress.percent_complete !== undefined && ` (${Math.round(progress.percent_complete)}%)`}
                </p>
                {progress.status === 'completed' && (
                  <span className="badge badge-success text-xs">Completed</span>
                )}
              </div>

              {/* Render performance metrics */}
              {renderPerformanceMetrics()}
            </>
          )}

          {progress.status === 'error' && progress.error && (
            <div className="p-3 bg-red-50 border border-red-200 rounded-md">
              <p className="text-xs text-red-500 font-medium">Error: {progress.error}</p>
            </div>
          )}

          {connectionError && (
            <div className="p-3 bg-amber-50 border border-amber-200 rounded-md">
              <p className="text-xs text-amber-600 font-medium">Connection issue: {connectionError}</p>
              <p className="text-xs text-amber-600">The progress updates may not be current.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default RagProgressIndicator;
