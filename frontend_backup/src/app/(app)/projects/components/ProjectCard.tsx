'use client';

import type React from 'react';
import Link from 'next/link';
import { Eye, Trash2, MessageSquareText, Settings2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import type { Project } from '@/types';
import { format } from 'date-fns';
import DeleteProjectDialog from './DeleteProjectDialog';
import { useState } from 'react';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip';


interface ProjectCardProps {
  project: Project;
  onDelete: (projectId: string) => Promise<void>;
}

export default function ProjectCard({ project, onDelete }: ProjectCardProps) {
  const [isDeleteDialogOpen, setIsDeleteDialogOpen] = useState(false);

  const handleDeleteConfirm = async () => {
    await onDelete(project.id);
    setIsDeleteDialogOpen(false);
  };

  return (
    <>
    <TooltipProvider>
      <Card className="flex flex-col h-full shadow-lg hover:shadow-xl transition-shadow duration-300">
        <CardHeader>
          <CardTitle className="truncate text-xl">{project.name}</CardTitle>
          <CardDescription>
            Created: {project.createdAt ? format(new Date(project.createdAt), 'PP') : 'Unknown date'}
          </CardDescription>
        </CardHeader>
        <CardContent className="flex-grow">
          <div className="space-y-2">
            <div className="text-sm text-muted-foreground">
              Scraped Sessions: <Badge variant="secondary">{project.scrapedSessionsCount}</Badge>
            </div>
            <div className="text-sm text-muted-foreground">
              RAG Status: <Badge variant={project.ragStatus === 'Enabled' ? 'default' : 'outline'} className={project.ragStatus === 'Enabled' ? 'bg-green-600/80 text-primary-foreground' : ''}>{project.ragStatus}</Badge>
            </div>
          </div>
        </CardContent>
        <CardFooter className="flex justify-end gap-2 border-t pt-4">
          <Tooltip>
            <TooltipTrigger asChild>
              <Button variant="outline" size="icon" asChild>
                <Link href={`/projects/${project.id}`}>
                  <Eye className="h-4 w-4" />
                  <span className="sr-only">View Details</span>
                </Link>
              </Button>
            </TooltipTrigger>
            <TooltipContent>View Details</TooltipContent>
          </Tooltip>

          {project.ragStatus === 'Enabled' && (
             <Tooltip>
              <TooltipTrigger asChild>
                <Button variant="outline" size="icon" asChild>
                  <Link href={`/projects/${project.id}/rag`}>
                    <MessageSquareText className="h-4 w-4" />
                    <span className="sr-only">Open RAG Chat</span>
                  </Link>
                </Button>
              </TooltipTrigger>
              <TooltipContent>Open RAG Chat</TooltipContent>
            </Tooltip>
          )}
          <Tooltip>
            <TooltipTrigger asChild>
              <Button variant="destructive" size="icon" onClick={() => setIsDeleteDialogOpen(true)}>
                <Trash2 className="h-4 w-4" />
                <span className="sr-only">Delete Project</span>
              </Button>
            </TooltipTrigger>
            <TooltipContent>Delete Project</TooltipContent>
          </Tooltip>
        </CardFooter>
      </Card>
      </TooltipProvider>
      <DeleteProjectDialog
        isOpen={isDeleteDialogOpen}
        onClose={() => setIsDeleteDialogOpen(false)}
        onConfirm={handleDeleteConfirm}
        projectName={project.name}
      />
    </>
  );
}
