'use client';

import type React from 'react';
import { useState } from 'react';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Download, Trash2, Eye } from 'lucide-react';
import type { ScrapedSession } from '@/types';
import { format } from 'date-fns';
import { Skeleton } from '@/components/ui/skeleton';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '@/components/ui/dialog';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip';


interface ScrapedSessionsTableProps {
  sessions: ScrapedSession[];
  isLoading: boolean;
  onDeleteSession: (sessionId: string) => Promise<void>;
}

export default function ScrapedSessionsTable({ sessions, isLoading, onDeleteSession }: ScrapedSessionsTableProps) {
  const [sessionToDelete, setSessionToDelete] = useState<ScrapedSession | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);
  const [viewingSession, setViewingSession] = useState<ScrapedSession | null>(null);


  const handleDeleteConfirm = async () => {
    if (!sessionToDelete) return;
    setIsDeleting(true);
    await onDeleteSession(sessionToDelete.id);
    setIsDeleting(false);
    setSessionToDelete(null);
  };

  const handleDownloadJson = (session: ScrapedSession) => {
    if (!session.structuredData) {
      alert("No structured data available for download.");
      return;
    }
    const jsonString = JSON.stringify(session.structuredData, null, 2);
    const blob = new Blob([jsonString], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${session.projectId}-${session.id}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  if (isLoading) {
    return (
      <div className="space-y-2">
        {[...Array(3)].map((_, i) => (
          <div key={i} className="flex items-center justify-between p-2 border rounded-md">
            <div className="flex-1 space-y-1">
              <Skeleton className="h-4 w-3/4" />
              <Skeleton className="h-3 w-1/2" />
            </div>
            <Skeleton className="h-8 w-20" />
          </div>
        ))}
      </div>
    );
  }

  if (sessions.length === 0) {
    return <p className="text-muted-foreground text-center py-4">No data scraped for this project yet.</p>;
  }

  return (
    <>
    <TooltipProvider>
      <ScrollArea className="border rounded-md">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>URL</TableHead>
              <TableHead>Scraped At</TableHead>
              <TableHead>Status</TableHead>
              <TableHead className="text-right">Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {sessions.map((session) => (
              <TableRow key={session.id}>
                <TableCell className="max-w-xs truncate">
                  <a href={session.url} target="_blank" rel="noopener noreferrer" className="hover:underline" title={session.url}>
                    {session.url}
                  </a>
                </TableCell>
                <TableCell>
                  {session.scrapedAt ?
                    (() => {
                      try {
                        return format(new Date(session.scrapedAt), 'Pp');
                      } catch (e) {
                        console.error('Invalid date format:', session.scrapedAt);
                        return 'Invalid date';
                      }
                    })()
                    : 'N/A'}
                </TableCell>
                <TableCell>
                  <Badge variant={session.status === 'Embedded for RAG' ? 'default' : 'secondary'}
                    className={session.status === 'Embedded for RAG' ? 'bg-green-600/80 text-primary-foreground' : session.status === 'Error' ? 'bg-destructive text-destructive-foreground' : ''}
                  >
                    {session.status}
                  </Badge>
                </TableCell>
                <TableCell className="text-right space-x-1">
                   <Tooltip>
                    <TooltipTrigger asChild>
                        <Button variant="ghost" size="icon" onClick={() => setViewingSession(session)}>
                            <Eye className="h-4 w-4" />
                            <span className="sr-only">View Data</span>
                        </Button>
                    </TooltipTrigger>
                    <TooltipContent>View Scraped Data</TooltipContent>
                  </Tooltip>
                  <Tooltip>
                    <TooltipTrigger asChild>
                        <Button variant="ghost" size="icon" onClick={() => handleDownloadJson(session)} disabled={!session.structuredData}>
                            <Download className="h-4 w-4" />
                            <span className="sr-only">Download JSON</span>
                        </Button>
                    </TooltipTrigger>
                    <TooltipContent>Download JSON</TooltipContent>
                  </Tooltip>
                  <Tooltip>
                    <TooltipTrigger asChild>
                        <Button variant="ghost" size="icon" onClick={() => setSessionToDelete(session)}>
                            <Trash2 className="h-4 w-4 text-destructive" />
                            <span className="sr-only">Delete Session</span>
                        </Button>
                    </TooltipTrigger>
                    <TooltipContent>Delete Session</TooltipContent>
                  </Tooltip>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </ScrollArea>
      </TooltipProvider>

      {sessionToDelete && (
        <AlertDialog open={!!sessionToDelete} onOpenChange={() => setSessionToDelete(null)}>
          <AlertDialogContent>
            <AlertDialogHeader>
              <AlertDialogTitle>Delete Scraped Session?</AlertDialogTitle>
              <AlertDialogDescription>
                Are you sure you want to delete the scraped data from URL: {sessionToDelete.url}? This action cannot be undone.
              </AlertDialogDescription>
            </AlertDialogHeader>
            <AlertDialogFooter>
              <AlertDialogCancel onClick={() => setSessionToDelete(null)} disabled={isDeleting}>Cancel</AlertDialogCancel>
              <AlertDialogAction onClick={handleDeleteConfirm} disabled={isDeleting} className="bg-destructive hover:bg-destructive/90">
                {isDeleting ? 'Deleting...' : 'Delete'}
              </AlertDialogAction>
            </AlertDialogFooter>
          </AlertDialogContent>
        </AlertDialog>
      )}

      {viewingSession && (
        <Dialog open={!!viewingSession} onOpenChange={() => setViewingSession(null)}>
            <DialogContent className="sm:max-w-2xl md:max-w-3xl lg:max-w-4xl max-h-[80vh]">
                <DialogHeader>
                    <DialogTitle>Scraped Data from: {viewingSession.url}</DialogTitle>
                    <DialogDescription>
                        Scraped at: {format(new Date(viewingSession.scrapedAt), 'PPP p')}
                    </DialogDescription>
                </DialogHeader>
                <ScrollArea className="max-h-[60vh] p-1 pr-4 rounded-md border">
                    <pre className="text-sm whitespace-pre-wrap break-all">
                        {JSON.stringify(viewingSession.structuredData || viewingSession.markdownContent || { message: "No viewable content." }, null, 2)}
                    </pre>
                </ScrollArea>
                 <div className="flex justify-end pt-4">
                    <Button onClick={() => setViewingSession(null)}>Close</Button>
                </div>
            </DialogContent>
        </Dialog>
      )}
    </>
  );
}
