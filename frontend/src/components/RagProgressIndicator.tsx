'use client';

import { useEffect, useState } from 'react';
import { Progress } from '@/components/ui/progress';
import { Card, CardContent, CardHeader, CardTitle, CardDescription, CardFooter } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { AlertCircle, CheckCircle, Loader2 } from 'lucide-react';
import { API_URL } from '@/lib/api';

interface RagProgressIndicatorProps {
  projectId: string;
  sessionId: string;
  onComplete?: () => void;
  className?: string;
}

interface ProgressData {
  status: 'idle' | 'processing' | 'completed' | 'error';
  message: string;
  current_chunk?: number;
  total_chunks?: number;
  percent_complete?: number;
  error?: string;
  performance_metrics?: {
    chunks_per_second?: number;
    processing_time?: number;
    batch_size?: number;
    total_batches?: number;
  };
}

export function RagProgressIndicator({ projectId, sessionId, onComplete, className = '' }: RagProgressIndicatorProps) {
  const [progress, setProgress] = useState<ProgressData>({
    status: 'idle',
    message: 'Waiting to start RAG ingestion...',
    current_chunk: 0,
    total_chunks: 0,
    percent_complete: 0
  });
  const [socket, setSocket] = useState<WebSocket | null>(null);
  const [connectionError, setConnectionError] = useState<string | null>(null);

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
  }, [projectId, sessionId, onComplete]);

  // Render different UI based on status
  const renderStatusIcon = () => {
    switch (progress.status) {
      case 'processing':
        return <Loader2 className="h-5 w-5 animate-spin text-blue-500" />;
      case 'completed':
        return <CheckCircle className="h-5 w-5 text-green-500" />;
      case 'error':
        return <AlertCircle className="h-5 w-5 text-red-500" />;
      default:
        return null;
    }
  };

  const getStatusBadge = () => {
    switch (progress.status) {
      case 'idle':
        return <Badge variant="outline">Idle</Badge>;
      case 'processing':
        return <Badge variant="secondary">Processing</Badge>;
      case 'completed':
        return <Badge variant="success">Completed</Badge>;
      case 'error':
        return <Badge variant="destructive">Error</Badge>;
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
          <Badge variant="outline" className="text-xs">
            {chunks_per_second.toFixed(2)} chunks/sec
          </Badge>
        )}
        {processing_time !== undefined && (
          <Badge variant="outline" className="text-xs">
            {processing_time.toFixed(2)}s processing time
          </Badge>
        )}
        {batch_size !== undefined && (
          <Badge variant="outline" className="text-xs">
            Batch size: {batch_size}
          </Badge>
        )}
        {total_batches !== undefined && (
          <Badge variant="outline" className="text-xs">
            {total_batches} batches
          </Badge>
        )}
      </div>
    );
  };

  return (
    <Card className={className || "w-full"}>
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg">RAG Ingestion Progress</CardTitle>
          {getStatusBadge()}
        </div>
        {progress.message && (
          <CardDescription>{progress.message}</CardDescription>
        )}
      </CardHeader>
      <CardContent>
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
              <Progress
                value={progress.status === 'completed' ? 100 : (progress.percent_complete || 0)}
                className="h-2"
                // Add color based on status
                style={{
                  backgroundColor: progress.status === 'error' ? 'rgba(239, 68, 68, 0.2)' : undefined,
                  '--progress-foreground': progress.status === 'completed'
                    ? 'hsl(var(--success))'
                    : progress.status === 'error'
                      ? 'hsl(var(--destructive))'
                      : undefined
                } as React.CSSProperties}
              />
              <div className="flex justify-between items-center">
                <p className="text-xs text-muted-foreground">
                  {progress.current_chunk} of {progress.total_chunks} chunks processed
                  {progress.percent_complete !== undefined && ` (${Math.round(progress.percent_complete)}%)`}
                </p>
                {progress.status === 'completed' && (
                  <Badge variant="success" className="text-xs">Completed</Badge>
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
      </CardContent>
    </Card>
  );
}
