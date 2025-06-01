import React, { memo, useRef, useEffect, useState } from 'react';
import ChartRenderer from './ChartRenderer';

/**
 * A stable wrapper for ChartRenderer that prevents unnecessary re-renders
 * and chart refreshing when parent components update
 */
const StableChartRenderer = memo(({ chartData, className = "" }) => {
  const [stableChartData, setStableChartData] = useState(null);
  const chartDataRef = useRef(null);

  useEffect(() => {
    // Only update if the chart data has actually changed
    const currentDataString = JSON.stringify(chartData);
    const previousDataString = JSON.stringify(chartDataRef.current);
    
    if (currentDataString !== previousDataString) {
      chartDataRef.current = chartData;
      setStableChartData(chartData);
    }
  }, [chartData]);

  // Don't render anything if we don't have stable chart data yet
  if (!stableChartData) {
    return null;
  }

  return <ChartRenderer chartData={stableChartData} className={className} />;
}, (prevProps, nextProps) => {
  // Custom comparison function to prevent unnecessary re-renders
  return JSON.stringify(prevProps.chartData) === JSON.stringify(nextProps.chartData) &&
         prevProps.className === nextProps.className;
});

StableChartRenderer.displayName = 'StableChartRenderer';

export default StableChartRenderer;
