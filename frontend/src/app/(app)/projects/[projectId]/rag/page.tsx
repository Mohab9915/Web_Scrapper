'use client';

import React, { useState, useEffect, useCallback, useRef } from 'react';
import { useParams, useRouter } from 'next/navigation';
import Link from 'next/link';
import { ArrowLeft, Send, Loader2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { getProjectById, getChatMessages, postChatMessage, queryRAG } from '@/lib/api';
import type { Project, ChatMessage } from '@/types';
import { useToast } from '@/hooks/use-toast';
import { Skeleton } from '@/components/ui/skeleton';
import ChatMessageCard from './components/ChatMessageCard';

export default function ProjectRagPage() {
  const params = useParams();
  const router = useRouter();
  const projectId = params.projectId as string;
  const { toast } = useToast();

  const [project, setProject] = useState<Project | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [newMessage, setNewMessage] = useState('');
  const [isLoadingProject, setIsLoadingProject] = useState(true);
  const [isLoadingMessages, setIsLoadingMessages] = useState(true);
  const [isSendingMessage, setIsSendingMessage] = useState(false);

  const scrollAreaRef = useRef<HTMLDivElement>(null);

  const fetchProjectDetails = useCallback(async () => {
    if (!projectId) return;
    setIsLoadingProject(true);
    try {
      const fetchedProject = await getProjectById(projectId);
      if (fetchedProject) {
        if (fetchedProject.ragStatus !== 'Enabled') {
          toast({ title: 'RAG Disabled', description: 'RAG is not enabled for this project. Redirecting...', variant: 'destructive' });
          router.push(`/projects/${projectId}`);
          return;
        }
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

  const fetchMessages = useCallback(async () => {
    if (!projectId) return;
    setIsLoadingMessages(true);
    try {
      const fetchedMessages = await getChatMessages(projectId);
      setMessages(fetchedMessages);
    } catch (error) {
      toast({ title: 'Error', description: 'Failed to fetch chat messages.', variant: 'destructive' });
    } finally {
      setIsLoadingMessages(false);
    }
  }, [projectId, toast]);

  useEffect(() => {
    fetchProjectDetails();
    fetchMessages();
  }, [fetchProjectDetails, fetchMessages]);

  useEffect(() => {
    if (scrollAreaRef.current) {
      scrollAreaRef.current.scrollTo({ top: scrollAreaRef.current.scrollHeight, behavior: 'smooth' });
    }
  }, [messages]);

  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newMessage.trim() || !project || isSendingMessage) return;

    setIsSendingMessage(true);
    const optimisticUserMessage: ChatMessage = {
      id: `temp-${Date.now()}`,
      role: 'user',
      content: newMessage,
      timestamp: new Date().toISOString(),
    };
    setMessages(prev => [...prev, optimisticUserMessage]);
    const messageToSend = newMessage;
    setNewMessage('');

    try {
      // Query the RAG system directly
      const ragResponse = await queryRAG(project.id, messageToSend);

      // Create user message with proper ID
      const userMessage: ChatMessage = {
        ...optimisticUserMessage,
        id: `msg_${Date.now()}`,
      };

      // Create assistant message from RAG response
      const assistantMessage: ChatMessage = {
        id: `msg_${Date.now() + 1}`,
        role: 'assistant',
        content: ragResponse.answer,
        timestamp: new Date().toISOString(),
        cost: ragResponse.generation_cost,
        sources: ragResponse.source_documents?.map(doc => doc.metadata.url) || [],
      };

      // Update messages state
      setMessages(prev =>
        prev.filter(m => m.id !== optimisticUserMessage.id).concat([
          userMessage,
          assistantMessage
        ])
      );
    } catch (error) {
      console.error('RAG query error:', error);
      toast({
        title: 'Error',
        description: error instanceof Error ? error.message : 'Failed to send message. Please try again.',
        variant: 'destructive'
      });
      // Remove the optimistic message on error
      setMessages(prev => prev.filter(m => m.id !== optimisticUserMessage.id));
    } finally {
      setIsSendingMessage(false);
    }
  };

  if (isLoadingProject || !project) {
    return (
      <div className="container mx-auto py-8 space-y-6">
        <Skeleton className="h-10 w-40 mb-4" />
        <Card className="flex flex-col" style={{ height: 'calc(100vh - 12rem)' }}>
          <CardHeader>
            <Skeleton className="h-8 w-3/4" />
            <Skeleton className="h-4 w-1/2 mt-2" />
          </CardHeader>
          <CardContent className="flex-grow p-4 space-y-4">
            <Skeleton className="h-16 w-full" />
            <Skeleton className="h-20 w-full" />
            <Skeleton className="h-12 w-full" />
          </CardContent>
          <div className="p-4 border-t">
            <Skeleton className="h-10 w-full" />
          </div>
        </Card>
      </div>
    );
  }

  return (
    <div className="container mx-auto py-8 h-full flex flex-col">
      <Button variant="outline" asChild className="mb-4 self-start">
        <Link href={`/projects/${project.id}`}>
          <ArrowLeft className="mr-2 h-4 w-4" /> Back to Project Details
        </Link>
      </Button>

      <Card className="flex-grow flex flex-col shadow-xl">
        <CardHeader className="border-b">
          <CardTitle>RAG Chat for: {project.name}</CardTitle>
          <CardDescription>Ask questions about the data scraped in this project.</CardDescription>
        </CardHeader>

        <CardContent className="flex-grow p-0 overflow-hidden">
          <ScrollArea className="h-full p-4" ref={scrollAreaRef}>
            {isLoadingMessages ? (
              <div className="space-y-4">
                <ChatMessageCard.Skeleton />
                <ChatMessageCard.Skeleton role="assistant" />
                <ChatMessageCard.Skeleton />
              </div>
            ) : messages.length > 0 ? (
              <div className="space-y-4">
                {messages.map((msg) => (
                  <ChatMessageCard key={msg.id} message={msg} />
                ))}
                {isSendingMessage && messages[messages.length-1]?.role === 'user' && (
                   <ChatMessageCard.Skeleton role="assistant" isTyping={true} />
                )}
              </div>
            ) : (
              <div className="flex flex-col items-center justify-center h-full text-center">
                <Avatar className="w-16 h-16 mb-4">
                  <AvatarImage src={`https://picsum.photos/seed/${project.id}/64`} data-ai-hint="robot avatar" />
                  <AvatarFallback>AI</AvatarFallback>
                </Avatar>
                <p className="text-lg font-medium">No messages yet.</p>
                <p className="text-muted-foreground">Start the conversation by asking a question below.</p>
              </div>
            )}
          </ScrollArea>
        </CardContent>

        <form onSubmit={handleSendMessage} className="p-4 border-t bg-background">
          <div className="flex items-center gap-2">
            <Input
              type="text"
              placeholder="Ask a question about this project's data..."
              value={newMessage}
              onChange={(e) => setNewMessage(e.target.value)}
              className="flex-grow"
              disabled={isSendingMessage}
            />
            <Button type="submit" disabled={!newMessage.trim() || isSendingMessage}>
              {isSendingMessage ? (
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              ) : (
                <Send className="mr-2 h-4 w-4" />
              )}
              Send
            </Button>
          </div>
           {/* Cost display */}
           <p className="text-xs text-muted-foreground mt-2 text-right">
            Model: gpt-4o-mini | Using Azure OpenAI Service
          </p>
        </form>
      </Card>
    </div>
  );
}
