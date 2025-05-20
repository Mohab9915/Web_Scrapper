'use client';

import { useState } from 'react';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import { CacheStatsDisplay } from '@/components/CacheStatsDisplay';
import { Settings, Database, RefreshCw, Server } from 'lucide-react';

export default function AdminPage() {
  const [apiEndpoint, setApiEndpoint] = useState('http://localhost:8000/api/v1');
  const [embeddingBatchSize, setEmbeddingBatchSize] = useState('20');
  const [cacheExpiryHours, setCacheExpiryHours] = useState('24');
  const [enableLogging, setEnableLogging] = useState(true);
  const [enableWebsockets, setEnableWebsockets] = useState(true);

  // These settings would typically be saved to localStorage or a backend API
  const saveSettings = () => {
    // In a real implementation, this would save to the backend
    console.log('Saving settings:', {
      apiEndpoint,
      embeddingBatchSize,
      cacheExpiryHours,
      enableLogging,
      enableWebsockets
    });

    // Show a toast notification
    alert('Settings saved successfully!');
  };

  return (
    <div className="container mx-auto py-10">
      <h1 className="text-3xl font-bold mb-6">Admin Settings</h1>
      
      <Tabs defaultValue="general" className="w-full">
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="general" className="flex items-center gap-2">
            <Settings className="h-4 w-4" />
            General
          </TabsTrigger>
          <TabsTrigger value="cache" className="flex items-center gap-2">
            <Database className="h-4 w-4" />
            Cache
          </TabsTrigger>
          <TabsTrigger value="system" className="flex items-center gap-2">
            <Server className="h-4 w-4" />
            System
          </TabsTrigger>
        </TabsList>
        
        {/* General Settings Tab */}
        <TabsContent value="general" className="space-y-4 mt-6">
          <Card>
            <CardHeader>
              <CardTitle>API Configuration</CardTitle>
              <CardDescription>
                Configure the API endpoints and authentication settings
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="api-endpoint">API Endpoint</Label>
                <Input 
                  id="api-endpoint" 
                  value={apiEndpoint} 
                  onChange={(e) => setApiEndpoint(e.target.value)} 
                  placeholder="http://localhost:8000/api/v1"
                />
                <p className="text-sm text-muted-foreground">
                  The base URL for the backend API
                </p>
              </div>
              
              <div className="flex items-center space-x-2">
                <Switch 
                  id="websockets" 
                  checked={enableWebsockets} 
                  onCheckedChange={setEnableWebsockets} 
                />
                <Label htmlFor="websockets">Enable WebSocket Connections</Label>
              </div>
              
              <Button onClick={saveSettings}>Save Settings</Button>
            </CardContent>
          </Card>
        </TabsContent>
        
        {/* Cache Settings Tab */}
        <TabsContent value="cache" className="space-y-4 mt-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Card>
              <CardHeader>
                <CardTitle>Cache Configuration</CardTitle>
                <CardDescription>
                  Configure web page caching settings
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="cache-expiry">Cache Expiry (hours)</Label>
                  <Input 
                    id="cache-expiry" 
                    type="number" 
                    value={cacheExpiryHours} 
                    onChange={(e) => setCacheExpiryHours(e.target.value)} 
                    min="1" 
                    max="720"
                  />
                  <p className="text-sm text-muted-foreground">
                    How long cached web pages should be stored before refreshing
                  </p>
                </div>
                
                <div className="pt-4">
                  <Button 
                    variant="outline" 
                    className="w-full"
                    onClick={() => {
                      // This would clear the cache in a real implementation
                      alert('Cache cleared successfully!');
                    }}
                  >
                    <RefreshCw className="h-4 w-4 mr-2" />
                    Clear Cache
                  </Button>
                </div>
                
                <Button onClick={saveSettings} className="w-full">Save Cache Settings</Button>
              </CardContent>
            </Card>
            
            {/* Cache Statistics */}
            <CacheStatsDisplay refreshInterval={30000} />
          </div>
        </TabsContent>
        
        {/* System Settings Tab */}
        <TabsContent value="system" className="space-y-4 mt-6">
          <Card>
            <CardHeader>
              <CardTitle>RAG System Configuration</CardTitle>
              <CardDescription>
                Configure Retrieval-Augmented Generation settings
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="embedding-batch-size">Embedding Batch Size</Label>
                <Input 
                  id="embedding-batch-size" 
                  type="number" 
                  value={embeddingBatchSize} 
                  onChange={(e) => setEmbeddingBatchSize(e.target.value)} 
                  min="1" 
                  max="100"
                />
                <p className="text-sm text-muted-foreground">
                  Number of chunks to process in a single API call (recommended: 10-30)
                </p>
              </div>
              
              <div className="flex items-center space-x-2">
                <Switch 
                  id="enable-logging" 
                  checked={enableLogging} 
                  onCheckedChange={setEnableLogging} 
                />
                <Label htmlFor="enable-logging">Enable Detailed Logging</Label>
              </div>
              
              <Button onClick={saveSettings}>Save System Settings</Button>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
