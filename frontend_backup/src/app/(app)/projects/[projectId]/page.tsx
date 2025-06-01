'use client';

import type React from 'react';
import { useState, useEffect, useCallback } from 'react';
import { useParams, useRouter } from 'next/navigation';
import Link from 'next/link';
import { ArrowLeft, Edit3, PlusCircle, AlertTriangle, BotMessageSquare } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Switch } from '@/components/ui/switch';
import { Label } from '@/components/ui/label';
import { Input } from '@/components/ui/input';
import {
  getProjectById,
  updateProjectRAGStatus,
  getScrapedSessions,
  initiateInteractiveScrape as apiInitiateInteractiveScrape,
  executeScrape as apiExecuteScrape,
  deleteScrapedSession as apiDeleteScrapedSession,
  updateProjectName as apiUpdateProjectName,
} from '@/lib/api';
import type { Project, ScrapedSession } from '@/types';
import { useToast } from '@/hooks/use-toast';
import ScrapedSessionsTable from './components/ScrapedSessionsTable';
import InteractiveScrapeModal from './components/InteractiveScrapeModal';
import { format } from 'date-fns';
import { Skeleton } from '@/components/ui/skeleton';
import { RagProgressIndicator } from '@/components/RagProgressIndicator';
import EditProjectNameDialog from './components/EditProjectNameDialog';

export default function ProjectDetailPage() {
  const params = useParams();
  const router = useRouter();
  const projectId = params.projectId as string;
  const { toast } = useToast();

  const [project, setProject] = useState<Project | null>(null);
  const [sessions, setSessions] = useState<ScrapedSession[]>([]);
  const [isLoadingProject, setIsLoadingProject] = useState(true);
  const [isLoadingSessions, setIsLoadingSessions] = useState(true);
  const [isRagUpdating, setIsRagUpdating] = useState(false);
  const [newUrl, setNewUrl] = useState('');
  const [isScrapingModalOpen, setIsScrapingModalOpen] = useState(false);
  const [interactiveScrapeInfo, setInteractiveScrapeInfo] = useState<{ url: string; sessionId: string } | null>(null);
  const [isEditNameDialogOpen, setIsEditNameDialogOpen] = useState(false);
  const [activeRagSession, setActiveRagSession] = useState<{ projectId: string; sessionId: string } | null>(null);


  const fetchProjectData = useCallback(async () => {
    if (!projectId) return;
    setIsLoadingProject(true);
    try {
      const fetchedProject = await getProjectById(projectId);
      if (fetchedProject) {
        setProject(fetchedProject);
      } else {
        toast({ title: 'Error', description: 'Project not found.', variant: 'destructive' });
        router.push('/projects');
      }
    } catch (error) {
      toast({ title: 'Error', description: 'Failed to fetch project details.', variant: 'destructive' });
    } finally {
      setIsLoadingProject(false);
    }
  }, [projectId, toast, router]);

  const fetchSessions = useCallback(async () => {
    if (!projectId) return;
    setIsLoadingSessions(true);
    try {
      const fetchedSessions = await getScrapedSessions(projectId);
      setSessions(fetchedSessions);
    } catch (error) {
      toast({ title: 'Error', description: 'Failed to fetch scraped sessions.', variant: 'destructive' });
    } finally {
      setIsLoadingSessions(false);
    }
  }, [projectId, toast]);

  useEffect(() => {
    fetchProjectData();
    fetchSessions();
  }, [fetchProjectData, fetchSessions]);

  const handleRagToggle = async (enabled: boolean) => {
    if (!project) return;
    setIsRagUpdating(true);
    try {
      const updatedProject = await updateProjectRAGStatus(project.id, enabled);
      if (updatedProject) {
        setProject(updatedProject);
        toast({
          title: 'Success',
          description: `RAG ${enabled ? 'enabled' : 'disabled'} with Azure OpenAI integration.`
        });
        fetchSessions(); // Refresh sessions to show updated RAG status
      }
    } catch (error) {
      console.error('RAG toggle error:', error);
      toast({
        title: 'Error',
        description: error instanceof Error ? error.message : 'Failed to update RAG status.',
        variant: 'destructive'
      });
      // Revert the UI toggle state on error
      setProject(prev => prev ? {...prev, ragStatus: prev.ragStatus === 'Enabled' ? 'Disabled' : 'Enabled'} : null);
    } finally {
      setIsRagUpdating(false);
    }
  };

  const handleStartInteractiveScrape = async () => {
    if (!newUrl.trim() || !project) return;

    // Validate URL format
    let url = newUrl.trim();
    if (!url.startsWith('http://') && !url.startsWith('https://')) {
      url = 'https://' + url;
    }

    try {
      toast({
        title: 'Initializing Interactive Scraping',
        description: `Preparing interactive browser for ${url}...`
      });

      // Initiate interactive scraping session
      const info = await apiInitiateInteractiveScrape(project.id, url);

      // Set the interactive scrape info and open the modal
      setInteractiveScrapeInfo({
        url: info.interactive_target_url,
        sessionId: info.session_id
      });
      setIsScrapingModalOpen(true);
      setNewUrl('');

    } catch (error) {
      console.error('Interactive scraping error:', error);
      toast({
        title: 'Error',
        description: error instanceof Error ? error.message : 'Failed to initiate interactive scraping.',
        variant: 'destructive'
      });
    }
  };

  const handleExecuteScrape = async (urlToScrape: string, sessionId: string, forceRefresh: boolean = false) => {
    if (!project) return false;

    try {
      // Show scraping toast
      toast({
        title: 'Scraping in Progress',
        description: `Extracting content from ${urlToScrape}${forceRefresh ? ' (bypassing cache)' : ''}. This may take a moment.`
      });

      // Execute scrape with Azure OpenAI credentials for embedding generation
      const newSession = await apiExecuteScrape(project.id, urlToScrape, sessionId, forceRefresh);

      // Update local state with the new session
      setSessions(prev => {
        // Check if this session already exists (might be an update)
        const existingIndex = prev.findIndex(s => s.id === newSession.id);
        if (existingIndex >= 0) {
          // Replace existing session
          const updated = [...prev];
          updated[existingIndex] = newSession;
          return updated;
        } else {
          // Add new session
          return [...prev, newSession];
        }
      });

      // Update project's scrapedSessionsCount
      setProject(prev => {
        if (!prev) return null;
        return {
          ...prev,
          scrapedSessionsCount: prev.scrapedSessionsCount + 1
        };
      });

      // Set active RAG session for progress tracking if RAG is enabled
      if (project.ragStatus === 'Enabled') {
        setActiveRagSession({
          projectId: project.id,
          sessionId: newSession.id
        });
      }

      // Show success toast
      toast({
        title: 'Scraping Successful',
        description: project.ragStatus === 'Enabled'
          ? `Page scraped and content is being processed for RAG. You can track the progress below.`
          : `Page scraped successfully. Enable RAG to query this content.`
      });

      // Refresh sessions list after a short delay to get updated status
      setTimeout(() => {
        fetchSessions();
      }, 2000);

      return true;
    } catch (error) {
      console.error('Scrape execution error:', error);

      toast({
        title: 'Scraping Failed',
        description: error instanceof Error
          ? error.message
          : `Failed to scrape ${urlToScrape}. Please try again.`,
        variant: 'destructive'
      });

      return false;
    }
  };

  const handleDeleteSession = async (sessionId: string) => {
    if (!project) return;
    try {
      await apiDeleteScrapedSession(project.id, sessionId);
      setSessions(prev => prev.filter(s => s.id !== sessionId));
      setProject(prev => prev ? {...prev, scrapedSessionsCount: Math.max(0, prev.scrapedSessionsCount - 1)} : null);
      toast({ title: 'Success', description: 'Scraped session deleted.' });
    } catch (error) {
      toast({ title: 'Error', description: 'Failed to delete session.', variant: 'destructive' });
    }
  };

  const handleUpdateProjectName = async (newName: string) => {
    if (!project || !newName.trim()) return;
    try {
      const updatedProject = await apiUpdateProjectName(project.id, newName);
      if (updatedProject) {
        setProject(updatedProject);
        toast({ title: 'Success', description: 'Project name updated.' });
        setIsEditNameDialogOpen(false);
      }
    } catch (error) {
      toast({ title: 'Error', description: 'Failed to update project name.', variant: 'destructive' });
    }
  };

  if (isLoadingProject || !project) {
    return (
      <div className="container mx-auto py-8 space-y-6">
        <Skeleton className="h-10 w-40" />
        <Card>
          <CardHeader>
            <Skeleton className="h-8 w-3/4" />
            <Skeleton className="h-4 w-1/2 mt-2" />
          </CardHeader>
          <CardContent className="space-y-4">
            <Skeleton className="h-6 w-1/4" />
            <Skeleton className="h-10 w-full" />
            <Skeleton className="h-10 w-1/2" />
          </CardContent>
        </Card>
        <Card>
          <CardHeader><Skeleton className="h-8 w-1/3" /></CardHeader>
          <CardContent><Skeleton className="h-40 w-full" /></CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="container mx-auto py-8 space-y-8">
      <div>
        <Button variant="outline" asChild className="mb-4">
          <Link href="/projects">
            <ArrowLeft className="mr-2 h-4 w-4" /> Back to Projects
          </Link>
        </Button>
        <div className="flex justify-between items-start">
            <div>
                <div className="flex items-center gap-2">
                    <h1 className="text-3xl font-bold tracking-tight">{project.name}</h1>
                    <Button variant="ghost" size="icon" onClick={() => setIsEditNameDialogOpen(true)}>
                        <Edit3 className="h-5 w-5" />
                        <span className="sr-only">Edit Project Name</span>
                    </Button>
                </div>
                <p className="text-muted-foreground">
                    Created: {format(new Date(project.createdAt), 'PPP p')}
                </p>
            </div>
            {(project.ragStatus === 'Enabled' || (project as any).ragEnabled === true) && (
                 <Button asChild>
                    <Link href={`/projects/${project.id}/rag`}>
                        <BotMessageSquare className="mr-2 h-4 w-4" /> Open RAG Chat
                    </Link>
                </Button>
            )}
        </div>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Project Settings</CardTitle>
          <CardDescription>Manage settings for this project.</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center space-x-2">
            <Switch
              id="rag-toggle"
              checked={project.ragStatus === 'Enabled' || (project as any).ragEnabled === true}
              onCheckedChange={handleRagToggle}
              disabled={isRagUpdating || project.ragStatus === 'Enabling'}
            />
            <Label htmlFor="rag-toggle" className="flex-grow">
              Enable RAG for this Project
              {project.ragStatus === 'Enabling' && <span className="ml-2 text-sm text-muted-foreground">(Processing...)</span>}
            </Label>
          </div>
          <p className="text-sm text-muted-foreground">
            When RAG is enabled, all scraped data for this project will be processed and made available for conversational querying.
          </p>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Add New URL to Scrape</CardTitle>
          <CardDescription>Enter a URL to start an interactive scraping session for "{project.name}".</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex flex-col sm:flex-row gap-2">
            <Input
              type="url"
              placeholder="https://example.com/page-to-scrape"
              value={newUrl}
              onChange={(e) => setNewUrl(e.target.value)}
              className="flex-grow"
            />
            <Button onClick={handleStartInteractiveScrape} disabled={!newUrl.trim()}>
              <PlusCircle className="mr-2 h-4 w-4" /> Start Interactive Scraping
            </Button>
          </div>
          <p className="mt-2 text-sm text-muted-foreground flex items-start">
            <AlertTriangle className="h-4 w-4 mr-1 mt-0.5 shrink-0 text-yellow-500" />
            Interactive scraping opens a simulated browser environment. Follow instructions within that environment to navigate and trigger scrapes.
          </p>
        </CardContent>
      </Card>

      {/* RAG Progress Indicator */}
      {activeRagSession && (
        <Card>
          <CardHeader>
            <CardTitle>RAG Processing Status</CardTitle>
            <CardDescription>Real-time progress of content processing for RAG</CardDescription>
          </CardHeader>
          <CardContent>
            <RagProgressIndicator
              projectId={activeRagSession.projectId}
              sessionId={activeRagSession.sessionId}
              onComplete={() => {
                setActiveRagSession(null);
                fetchSessions(); // Refresh sessions when processing completes
              }}
            />
          </CardContent>
        </Card>
      )}

      <Card>
        <CardHeader>
          <CardTitle>Scraped Sessions</CardTitle>
          <CardDescription>Data scraped for project "{project.name}".</CardDescription>
        </CardHeader>
        <CardContent>
          <ScrapedSessionsTable
            sessions={sessions}
            isLoading={isLoadingSessions}
            onDeleteSession={handleDeleteSession}
          />
        </CardContent>
      </Card>

      {interactiveScrapeInfo && (
        <InteractiveScrapeModal
          isOpen={isScrapingModalOpen}
          onClose={() => setIsScrapingModalOpen(false)}
          initialUrl={interactiveScrapeInfo.url}
          sessionId={interactiveScrapeInfo.sessionId}
          onExecuteScrape={handleExecuteScrape}
          projectName={project.name}
        />
      )}
      <EditProjectNameDialog
        isOpen={isEditNameDialogOpen}
        onClose={() => setIsEditNameDialogOpen(false)}
        currentName={project.name}
        onUpdate={handleUpdateProjectName}
      />
    </div>
  );
}
