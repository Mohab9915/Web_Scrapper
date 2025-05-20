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
import { Label } from '@/components/ui/label';

interface EditProjectNameDialogProps {
  isOpen: boolean;
  onClose: () => void;
  currentName: string;
  onUpdate: (newName: string) => Promise<void>;
}

export default function EditProjectNameDialog({ isOpen, onClose, currentName, onUpdate }: EditProjectNameDialogProps) {
  const [newName, setNewName] = useState(currentName);
  const [isUpdating, setIsUpdating] = useState(false);

  useEffect(() => {
    if (isOpen) {
      setNewName(currentName);
    }
  }, [isOpen, currentName]);

  const handleSubmit = async () => {
    if (!newName.trim() || newName.trim() === currentName) {
      onClose(); // Close if no change or empty
      return;
    }
    setIsUpdating(true);
    await onUpdate(newName.trim());
    setIsUpdating(false);
    // onClose will be called by parent upon successful update in ProjectDetailPage
  };

  const descriptionId = 'edit-project-name-description';

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-[425px]" aria-describedby={descriptionId}>
        <DialogTitle>Edit Project Name</DialogTitle>
        <DialogHeader>
          <DialogDescription id={descriptionId}>
            Change the name of your project. Make it descriptive!
          </DialogDescription>
        </DialogHeader>
        <div className="grid gap-4 py-4">
          <div className="grid grid-cols-4 items-center gap-4">
            <Label htmlFor="newProjectName" className="text-right">
              Name
            </Label>
            <Input
              id="newProjectName"
              value={newName}
              onChange={(e) => setNewName(e.target.value)}
              className="col-span-3"
              placeholder="e.g., Q1 Competitor Research"
            />
          </div>
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={onClose} disabled={isUpdating}>
            Cancel
          </Button>
          <Button onClick={handleSubmit} disabled={isUpdating || !newName.trim() || newName.trim() === currentName}>
            {isUpdating ? 'Saving...' : 'Save Changes'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
