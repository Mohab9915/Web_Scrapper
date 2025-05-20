'use client';

import type React from 'react';
import { useState } from 'react';
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
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea'; // For multiple URLs

interface CreateProjectDialogProps {
  isOpen: boolean;
  onClose: () => void;
  onCreate: (name: string, initialUrls?: string[]) => Promise<void>;
}

export default function CreateProjectDialog({ isOpen, onClose, onCreate }: CreateProjectDialogProps) {
  const [projectName, setProjectName] = useState('');
  const [initialUrlsText, setInitialUrlsText] = useState('');
  const [isCreating, setIsCreating] = useState(false);

  const handleSubmit = async () => {
    if (!projectName.trim()) {
      // Basic validation, consider react-hook-form for more complex forms
      alert('Project name is required.');
      return;
    }
    setIsCreating(true);
    const urls = initialUrlsText.split('\n').map(url => url.trim()).filter(url => url.length > 0);
    await onCreate(projectName, urls.length > 0 ? urls : undefined);
    setIsCreating(false);
    setProjectName('');
    setInitialUrlsText('');
    // onClose will be called by parent upon successful creation
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-[425px]">
        <DialogHeader>
          <DialogTitle>Create New Project</DialogTitle>
          <DialogDescription>
            Enter a name for your new project. You can optionally add initial URLs to scrape.
          </DialogDescription>
        </DialogHeader>
        <div className="grid gap-4 py-4">
          <div className="grid grid-cols-4 items-center gap-4">
            <Label htmlFor="projectName" className="text-right">
              Name
            </Label>
            <Input
              id="projectName"
              value={projectName}
              onChange={(e) => setProjectName(e.target.value)}
              className="col-span-3"
              placeholder="e.g., Q4 Market Research"
            />
          </div>
          <div className="grid grid-cols-4 items-center gap-4">
            <Label htmlFor="initialUrls" className="text-right">
              Initial URLs
              <span className="block text-xs text-muted-foreground">(optional, one per line)</span>
            </Label>
            <Textarea
              id="initialUrls"
              value={initialUrlsText}
              onChange={(e) => setInitialUrlsText(e.target.value)}
              className="col-span-3"
              placeholder="https://example.com/page1&#10;https://another.com/itemA"
              rows={3}
            />
          </div>
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={onClose} disabled={isCreating}>
            Cancel
          </Button>
          <Button onClick={handleSubmit} disabled={isCreating || !projectName.trim()}>
            {isCreating ? 'Creating...' : 'Create Project'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
