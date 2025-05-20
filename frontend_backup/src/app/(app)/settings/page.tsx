'use client';

import React, { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Button } from '@/components/ui/button';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { KeyRound, Save } from 'lucide-react';
import { useToast } from '@/hooks/use-toast';

// This is a placeholder for API key management and default LLM settings.
// In a real app, this would involve secure storage and backend interaction.

export default function SettingsPage() {
  const { toast } = useToast();
  const [apiKeys, setApiKeys] = useState({ openAIKey: '', googleAIKey: ''});
  const [defaultLlm, setDefaultLlm] = useState('gemini-2.0-flash'); // Matches genkit.ts

  const handleSaveSettings = () => {
    // In a real app, send this to a secure backend.
    // For this demo, we just show a toast.
    console.log('Saving settings:', { apiKeys, defaultLlm });
    toast({
      title: 'Settings Saved (Simulated)',
      description: 'API keys and default LLM preferences have been noted (client-side only for demo).',
    });
  };

  return (
    <div className="container mx-auto py-8 space-y-8">
      <h1 className="text-3xl font-bold tracking-tight">Global Settings</h1>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center">
            <KeyRound className="mr-2 h-5 w-5 text-primary" />
            API Key Management
          </CardTitle>
          <CardDescription>
            These keys are for demonstration purposes only and are stored client-side.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="openAIKey">OpenAI API Key</Label>
            <Input
              id="openAIKey"
              type="password"
              placeholder="sk-..."
              value={apiKeys.openAIKey}
              onChange={(e) => setApiKeys(prev => ({...prev, openAIKey: e.target.value}))}
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="googleAIKey">Google AI API Key</Label>
            <Input
              id="googleAIKey"
              type="password"
              placeholder="AIza..."
              value={apiKeys.googleAIKey}
              onChange={(e) => setApiKeys(prev => ({...prev, googleAIKey: e.target.value}))}
            />
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Default Language Model</CardTitle>
          <CardDescription>
            Select the default LLM to be used for RAG queries. This can sometimes be overridden per project.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="defaultLlm">Default LLM</Label>
            <Select value={defaultLlm} onValueChange={setDefaultLlm}>
              <SelectTrigger id="defaultLlm">
                <SelectValue placeholder="Select LLM" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="googleai/gemini-2.0-flash">Gemini 2.0 Flash (Google AI)</SelectItem>
                <SelectItem value="openai/gpt-4">GPT-4 (OpenAI - Placeholder)</SelectItem>
                <SelectItem value="openai/gpt-3.5-turbo">GPT-3.5 Turbo (OpenAI - Placeholder)</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>
      
      <div className="flex justify-end">
        <Button onClick={handleSaveSettings}>
          <Save className="mr-2 h-4 w-4" /> Save All Settings
        </Button>
      </div>
    </div>
  );
}
// Dummy export to satisfy module requirements if needed
// export const dummyExport = {};

