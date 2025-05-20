'use client';

import React, { useState, useRef, useEffect } from 'react';
import { Loader2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Alert, AlertDescription } from '@/components/ui/alert';

interface EmbeddedBrowserProps {
  url: string;
  onNavigate?: (newUrl: string) => void;
  isLoading?: boolean;
  height?: string | number;
  width?: string | number;
  className?: string;
}

export default function EmbeddedBrowser({
  url,
  onNavigate,
  isLoading = false,
  height = '600px',
  width = '100%',
  className = '',
}: EmbeddedBrowserProps) {
  const iframeRef = useRef<HTMLIFrameElement>(null);
  const [error, setError] = useState<string | null>(null);
  const [currentUrl, setCurrentUrl] = useState<string>(url);
  const [iframeLoading, setIframeLoading] = useState<boolean>(true);

  // Reset loading state when URL changes
  useEffect(() => {
    setIframeLoading(true);
    setError(null);
    setCurrentUrl(url);
  }, [url]);

  // Handle iframe load events
  const handleIframeLoad = () => {
    setIframeLoading(false);

    try {
      // Try to get the current URL from the iframe
      if (iframeRef.current?.contentWindow?.location.href) {
        const newUrl = iframeRef.current.contentWindow.location.href;

        // Only update if URL has changed
        if (newUrl !== currentUrl) {
          setCurrentUrl(newUrl);
          if (onNavigate) {
            onNavigate(newUrl);
          }
        }
      }
    } catch (e) {
      // Cross-origin restrictions might prevent accessing the iframe's location
      console.warn('Could not access iframe location due to cross-origin restrictions');
    }
  };

  // Handle iframe errors
  const handleIframeError = () => {
    setIframeLoading(false);
    setError('Failed to load the page. This could be due to cross-origin restrictions or the page is unavailable.');
  };

  return (
    <div className={`relative rounded-md overflow-hidden border ${className}`} style={{ height, width }}>
      {/* Loading overlay */}
      {(isLoading || iframeLoading) && (
        <div className="absolute inset-0 bg-background/80 flex items-center justify-center z-10">
          <div className="text-center">
            <Loader2 className="h-8 w-8 animate-spin text-primary mx-auto mb-2" />
            <p className="text-sm text-muted-foreground">Loading page...</p>
          </div>
        </div>
      )}

      {/* Error message */}
      {error && (
        <div className="absolute inset-0 bg-background/95 flex items-center justify-center z-10 p-4">
          <Alert variant="destructive" className="max-w-md">
            <AlertDescription>{error}</AlertDescription>
            <Button
              variant="outline"
              size="sm"
              className="mt-2"
              onClick={() => {
                setError(null);
                setIframeLoading(true);
                if (iframeRef.current) {
                  iframeRef.current.src = url;
                }
              }}
            >
              Try Again
            </Button>
          </Alert>
        </div>
      )}

      {/* The iframe - Using a div wrapper with fixed height and overflow auto instead of ScrollArea */}
      <div className="h-full w-full overflow-auto">
        <iframe
          ref={iframeRef}
          src={url}
          onLoad={handleIframeLoad}
          onError={handleIframeError}
          style={{
            width: '100%',
            height: '100%',
            minHeight: typeof height === 'string' ? height : `${height}px`,
            border: 'none',
            display: 'block', // Ensures no extra space below iframe
            overflow: 'auto' // Enable scrolling within the iframe
          }}
          sandbox="allow-same-origin allow-scripts allow-forms allow-popups"
          title="Interactive Browser"
        />
      </div>
    </div>
  );
}
