'use client';

import type React from 'react';
import { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Globe, Search, Loader2, Download, RefreshCw } from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip';
import { Switch } from '@/components/ui/switch';
import { Label } from '@/components/ui/label';
import EmbeddedBrowser from './EmbeddedBrowser';

interface InteractiveScrapeModalProps {
  isOpen: boolean;
  onClose: () => void;
  initialUrl: string;
  sessionId: string;
  projectName: string;
  onExecuteScrape: (urlToScrape: string, sessionId: string, forceRefresh?: boolean) => Promise<boolean>;
}

export default function InteractiveScrapeModal({
  isOpen,
  onClose,
  initialUrl,
  sessionId,
  projectName,
  onExecuteScrape,
}: InteractiveScrapeModalProps) {
  const [currentUrl, setCurrentUrl] = useState(initialUrl);
  const [displayUrl, setDisplayUrl] = useState(initialUrl); // For the "browser" content
  const [isLoadingPage, setIsLoadingPage] = useState(false);
  const [isScraping, setIsScraping] = useState(false);
  const [scrapeStatus, setScrapeStatus] = useState<'idle' | 'success' | 'error'>('idle');
  const [forceRefresh, setForceRefresh] = useState(false);

  useEffect(() => {
    setCurrentUrl(initialUrl);
    setDisplayUrl(initialUrl);
    setScrapeStatus('idle');
  }, [isOpen, initialUrl]);

  const handleNavigate = () => {
    setIsLoadingPage(true);
    // Simulate page load
    setTimeout(() => {
      setDisplayUrl(currentUrl);
      setIsLoadingPage(false);
      setScrapeStatus('idle');
    }, 1000 + Math.random() * 1000); // Random delay
  };

  const handleScrapeThisPage = async () => {
    setIsScraping(true);
    setScrapeStatus('idle');
    const success = await onExecuteScrape(displayUrl, sessionId, forceRefresh);
    setIsScraping(false);
    setScrapeStatus(success ? 'success' : 'error');
    if (success) {
      // Optionally close modal on successful scrape, or allow more scrapes.
      // For now, keep it open to allow further navigation/scraping.
      // onClose();
    }
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-3xl md:max-w-4xl lg:max-w-5xl h-[90vh] max-h-[90vh] flex flex-col p-0">
        <DialogHeader className="p-6 pb-0">
          <DialogTitle className="flex items-center">
            <Globe className="mr-2 h-5 w-5 text-primary" />
            Interactive Scraping for "{projectName}"
          </DialogTitle>
          <DialogDescription>
            Navigate the website below. When ready, click "Scrape This Page". Current Session ID: {sessionId}
          </DialogDescription>
        </DialogHeader>

        {/* Simulated Browser Address Bar */}
        <div className="flex items-center gap-2 px-6 py-3 border-b">
          <Input
            type="url"
            value={currentUrl}
            onChange={(e) => setCurrentUrl(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleNavigate()}
            className="flex-grow"
            placeholder="Enter URL and press Enter or click Go"
          />
          <Button onClick={handleNavigate} disabled={isLoadingPage}>
            {isLoadingPage ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : <Search className="h-4 w-4 mr-2" />}
            Go
          </Button>

          {/* Force refresh option */}
          <div className="flex items-center ml-2">
            <div className="flex items-center space-x-2">
              <Switch
                id="force-refresh"
                checked={forceRefresh}
                onCheckedChange={setForceRefresh}
              />
              <Label htmlFor="force-refresh" className="text-xs whitespace-nowrap cursor-pointer">
                <TooltipProvider>
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <div className="flex items-center">
                        <RefreshCw className="h-3 w-3 mr-1" />
                        Force Refresh
                      </div>
                    </TooltipTrigger>
                    <TooltipContent>
                      <p>Bypass cache and fetch fresh content</p>
                    </TooltipContent>
                  </Tooltip>
                </TooltipProvider>
              </Label>
            </div>
          </div>
        </div>

        {/* Real Browser Content Area */}
        <div className="flex-grow relative">
          <div className="absolute top-0 right-0 z-10 p-2">
            <TooltipProvider>
              <Tooltip>
                <TooltipTrigger asChild>
                  <Button
                    onClick={handleScrapeThisPage}
                    disabled={isLoadingPage || isScraping}
                    size="lg"
                    className="bg-green-600 hover:bg-green-700 text-white shadow-lg"
                  >
                    {isScraping ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : <Download className="h-4 w-4 mr-2" />}
                    {isScraping ? 'Scraping...' : 'Scrape This Page'}
                  </Button>
                </TooltipTrigger>
                <TooltipContent>
                  <p>Extract data from this page and add it to your project</p>
                </TooltipContent>
              </Tooltip>
            </TooltipProvider>
          </div>

          <EmbeddedBrowser
            url={displayUrl}
            isLoading={isLoadingPage}
            onNavigate={(newUrl) => {
              setCurrentUrl(newUrl);
              setDisplayUrl(newUrl);
              setScrapeStatus('idle');
            }}
            height="100%"
          />
        </div>

        <DialogFooter className="p-6 border-t flex flex-col sm:flex-row items-center justify-between w-full">
          <div className="text-sm flex items-center">
            {scrapeStatus === 'success' && (
              <div className="flex items-center">
                <Badge variant="success" className="mr-2">Success</Badge>
                <span className="text-green-600">Page scraped successfully!</span>
              </div>
            )}
            {scrapeStatus === 'error' && (
              <div className="flex items-center">
                <Badge variant="destructive" className="mr-2">Error</Badge>
                <span className="text-destructive">Scraping failed. Please try again.</span>
              </div>
            )}
            {scrapeStatus === 'idle' && (
              <span className="text-muted-foreground">
                Navigate to the content you want to extract, then click the "Scrape This Page" button.
              </span>
            )}
          </div>
          <div className="flex gap-2 mt-4 sm:mt-0">
            <Button
              variant="outline"
              onClick={onClose}
              disabled={isScraping}
            >
              {scrapeStatus === 'success' ? 'Done' : 'Cancel'}
            </Button>
            {scrapeStatus === 'success' && (
              <Button
                variant="default"
                onClick={() => {
                  // Reset the status to allow for more scraping
                  setScrapeStatus('idle');
                }}
              >
                Scrape Another Page
              </Button>
            )}
          </div>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
