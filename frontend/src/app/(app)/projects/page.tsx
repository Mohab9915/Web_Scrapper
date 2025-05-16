'use client';

import type React from 'react';
import { useState, useEffect } from 'react';
import { PlusCircle } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import CreateProjectDialog from './components/CreateProjectDialog';
import ProjectCard from './components/ProjectCard';
import { getProjects, createProject as apiCreateProject, deleteProject as apiDeleteProject } from '@/lib/api';
import type { Project } from '@/types';
import { useToast } from '@/hooks/use-toast';
import { Skeleton } from '@/components/ui/skeleton';

export default function ProjectsPage() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isCreateDialogOpen, setIsCreateDialogOpen] = useState(false);
  const { toast } = useToast();

  useEffect(() => {
    fetchProjects();
  }, []);

  const fetchProjects = async () => {
    setIsLoading(true);
    try {
      const fetchedProjects = await getProjects();
      setProjects(fetchedProjects);
    } catch (error) {
      toast({ title: 'Error', description: 'Failed to fetch projects.', variant: 'destructive' });
    } finally {
      setIsLoading(false);
    }
  };

  const handleCreateProject = async (name: string, initialUrls?: string[]) => {
    try {
      const newProject = await apiCreateProject(name, initialUrls);
      setProjects(prev => [...prev, newProject]);
      toast({ title: 'Success', description: `Project "${name}" created.` });
      setIsCreateDialogOpen(false);
      fetchProjects(); // Re-fetch to update counts etc.
    } catch (error) {
      toast({ title: 'Error', description: 'Failed to create project.', variant: 'destructive' });
    }
  };

  const handleDeleteProject = async (projectId: string) => {
    try {
      await apiDeleteProject(projectId);
      setProjects(prev => prev.filter(p => p.id !== projectId));
      toast({ title: 'Success', description: 'Project deleted.' });
    } catch (error) {
      toast({ title: 'Error', description: 'Failed to delete project.', variant: 'destructive' });
    }
  };

  return (
    <div className="container mx-auto py-8">
      <div className="flex justify-between items-center mb-8">
        <h1 className="text-3xl font-bold tracking-tight">My Projects</h1>
        <Button onClick={() => setIsCreateDialogOpen(true)}>
          <PlusCircle className="mr-2 h-5 w-5" /> Create New Project
        </Button>
      </div>

      {isLoading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {[...Array(3)].map((_, i) => (
            <Card key={i}>
              <CardHeader>
                <Skeleton className="h-6 w-3/4" />
                <Skeleton className="h-4 w-1/2" />
              </CardHeader>
              <CardContent>
                <Skeleton className="h-4 w-full mb-2" />
                <Skeleton className="h-4 w-2/3" />
                <div className="flex justify-end gap-2 mt-4">
                  <Skeleton className="h-10 w-24" />
                  <Skeleton className="h-10 w-20" />
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      ) : projects.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {projects.map((project) => (
            <ProjectCard key={project.id} project={project} onDelete={handleDeleteProject} />
          ))}
        </div>
      ) : (
        <Card className="col-span-full">
          <CardHeader>
            <CardTitle>No Projects Yet</CardTitle>
            <CardDescription>Get started by creating your first scraping project.</CardDescription>
          </CardHeader>
          <CardContent>
            <Button onClick={() => setIsCreateDialogOpen(true)} className="w-full sm:w-auto">
              <PlusCircle className="mr-2 h-5 w-5" /> Create Your First Project
            </Button>
          </CardContent>
        </Card>
      )}

      <CreateProjectDialog
        isOpen={isCreateDialogOpen}
        onClose={() => setIsCreateDialogOpen(false)}
        onCreate={handleCreateProject}
      />
    </div>
  );
}
