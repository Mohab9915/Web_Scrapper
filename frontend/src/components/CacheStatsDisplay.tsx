'use client';

import { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { Badge } from '@/components/ui/badge';
import { RefreshCw, Database, Clock } from 'lucide-react';
import { fetchCacheStats } from '@/lib/api';

interface CacheStats {
  total_entries: number;
  hit_count: number;
  miss_count: number;
  hit_rate: number;
}

interface CacheStatsDisplayProps {
  className?: string;
  refreshInterval?: number; // in milliseconds, if provided will auto-refresh
}

export function CacheStatsDisplay({ className = '', refreshInterval }: CacheStatsDisplayProps) {
  const [stats, setStats] = useState<CacheStats | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);

  const fetchStats = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const data = await fetchCacheStats();
      setStats(data);
      setLastUpdated(new Date());
    } catch (err) {
      console.error('Error fetching cache stats:', err);
      setError('Failed to load cache statistics');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    // Initial fetch
    fetchStats();
    
    // Set up auto-refresh if interval is provided
    if (refreshInterval) {
      const intervalId = setInterval(fetchStats, refreshInterval);
      
      // Clean up on unmount
      return () => clearInterval(intervalId);
    }
  }, [refreshInterval]);

  // Format the hit rate as a percentage
  const formatHitRate = (rate: number) => {
    return `${(rate * 100).toFixed(1)}%`;
  };

  // Format the last updated time
  const formatLastUpdated = () => {
    if (!lastUpdated) return 'Never';
    
    return lastUpdated.toLocaleTimeString();
  };

  // Determine hit rate color
  const getHitRateColor = (rate: number) => {
    if (rate >= 0.8) return 'text-green-600';
    if (rate >= 0.5) return 'text-amber-600';
    return 'text-red-600';
  };

  return (
    <Card className={className}>
      <CardHeader>
        <div className="flex justify-between items-center">
          <CardTitle className="text-lg flex items-center">
            <Database className="h-5 w-5 mr-2" />
            Cache Statistics
          </CardTitle>
          <Button 
            variant="outline" 
            size="sm" 
            onClick={fetchStats} 
            disabled={loading}
            className="h-8 px-2"
          >
            <RefreshCw className={`h-4 w-4 mr-1 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
        </div>
        <CardDescription>
          Web page cache performance metrics
        </CardDescription>
      </CardHeader>
      <CardContent>
        {error ? (
          <div className="p-3 bg-red-50 border border-red-200 rounded-md">
            <p className="text-sm text-red-600">{error}</p>
          </div>
        ) : !stats ? (
          <div className="flex justify-center items-center h-24">
            <RefreshCw className="h-6 w-6 animate-spin text-muted-foreground" />
          </div>
        ) : (
          <div className="space-y-4">
            {/* Hit Rate */}
            <div className="space-y-1">
              <div className="flex justify-between items-center">
                <span className="text-sm font-medium">Cache Hit Rate</span>
                <span className={`text-sm font-bold ${getHitRateColor(stats.hit_rate)}`}>
                  {formatHitRate(stats.hit_rate)}
                </span>
              </div>
              <Progress value={stats.hit_rate * 100} className="h-2" />
            </div>
            
            {/* Hit/Miss Counts */}
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-1">
                <span className="text-sm font-medium">Cache Hits</span>
                <div className="flex items-center">
                  <Badge variant="success" className="mr-2">Hits</Badge>
                  <span className="text-lg font-bold">{stats.hit_count}</span>
                </div>
              </div>
              <div className="space-y-1">
                <span className="text-sm font-medium">Cache Misses</span>
                <div className="flex items-center">
                  <Badge variant="destructive" className="mr-2">Misses</Badge>
                  <span className="text-lg font-bold">{stats.miss_count}</span>
                </div>
              </div>
            </div>
            
            {/* Total Entries */}
            <div className="pt-2 border-t">
              <div className="flex justify-between items-center">
                <span className="text-sm font-medium">Total Cached Pages</span>
                <span className="text-lg font-bold">{stats.total_entries}</span>
              </div>
            </div>
          </div>
        )}
      </CardContent>
      <CardFooter className="text-xs text-muted-foreground flex justify-between">
        <div className="flex items-center">
          <Clock className="h-3 w-3 mr-1" />
          Last updated: {formatLastUpdated()}
        </div>
        {stats && (
          <div>
            Total requests: {stats.hit_count + stats.miss_count}
          </div>
        )}
      </CardFooter>
    </Card>
  );
}
