import React, { useState, useEffect } from 'react';
import { fetchCacheStats } from '../lib/api';

function CacheStatsDisplay({ className = '', refreshInterval }) {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [lastUpdated, setLastUpdated] = useState(null);

  const fetchStats = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const data = await fetchCacheStats();
      setStats(data);
      setLastUpdated(new Date());
    } catch (err) {
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
  const formatHitRate = (rate) => {
    return `${(rate * 100).toFixed(1)}%`;
  };

  // Format the last updated time
  const formatLastUpdated = () => {
    if (!lastUpdated) return 'Never';
    
    return lastUpdated.toLocaleTimeString();
  };

  // Determine hit rate color
  const getHitRateColor = (rate) => {
    if (rate >= 0.8) return 'text-green-600';
    if (rate >= 0.5) return 'text-amber-600';
    return 'text-red-600';
  };

  return (
    <div className={`card ${className}`}>
      <div className="card-header">
        <div className="flex justify-between items-center">
          <h3 className="card-title text-lg flex items-center">
            <span className="mr-2">🗄️</span>
            Cache Statistics
          </h3>
          <button 
            className="btn btn-outline btn-sm"
            onClick={fetchStats} 
            disabled={loading}
          >
            <span className={`mr-1 ${loading ? 'animate-spin' : ''}`}>⟳</span>
            Refresh
          </button>
        </div>
        <p className="card-description">
          Web page cache performance metrics
        </p>
      </div>
      <div className="card-content">
        {error ? (
          <div className="p-3 bg-red-50 border border-red-200 rounded-md">
            <p className="text-sm text-red-600">{error}</p>
          </div>
        ) : !stats ? (
          <div className="flex justify-center items-center h-24">
            <span className="animate-spin text-gray-400">⟳</span>
          </div>
        ) : (
          <div className="space-y-4">
            {/* Hit Rate */}
            <div className="space-y-1">
              <div className="flex justify-between items-center">
                <span className="text-sm font-medium">Cache Hit Rate</span>
                <span className={`text-sm font-bold ${getHitRateColor(stats.hitRate)}`}>
                  {formatHitRate(stats.hitRate)}
                </span>
              </div>
              <div className="progress-bar">
                <div 
                  className="progress-bar-fill" 
                  style={{ width: `${stats.hitRate * 100}%` }}
                />
              </div>
            </div>
            
            {/* Hit/Miss Counts */}
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-1">
                <span className="text-sm font-medium">Cache Hits</span>
                <div className="flex items-center">
                  <span className="badge badge-success mr-2">Hits</span>
                  <span className="text-lg font-bold">{stats.hitCount}</span>
                </div>
              </div>
              <div className="space-y-1">
                <span className="text-sm font-medium">Cache Misses</span>
                <div className="flex items-center">
                  <span className="badge badge-error mr-2">Misses</span>
                  <span className="text-lg font-bold">{stats.missCount}</span>
                </div>
              </div>
            </div>
            
            {/* Total Entries */}
            <div className="pt-2 border-t">
              <div className="flex justify-between items-center">
                <span className="text-sm font-medium">Total Cached Pages</span>
                <span className="text-lg font-bold">{stats.totalEntries}</span>
              </div>
            </div>
          </div>
        )}
      </div>
      <div className="card-footer text-xs text-muted-foreground flex justify-between">
        <div className="flex items-center">
          <span className="mr-1">🕒</span>
          Last updated: {formatLastUpdated()}
        </div>
        {stats && (
          <div>
            Total requests: {stats.hitCount + stats.missCount}
          </div>
        )}
      </div>
    </div>
  );
}

export default CacheStatsDisplay;
