import React, { useEffect, useRef, useMemo } from 'react';
import Chart from 'chart.js/auto';

const ChartRenderer = ({ chartData, className = "" }) => {
  const canvasRef = useRef(null);
  const chartRef = useRef(null);

  // Memoize chart data to prevent unnecessary re-renders
  const memoizedChartData = useMemo(() => chartData, [JSON.stringify(chartData)]);

  useEffect(() => {
    console.log('ChartRenderer: useEffect triggered', { memoizedChartData, hasCanvas: !!canvasRef.current });

    if (!memoizedChartData || !canvasRef.current) {
      console.log('ChartRenderer: Early return - no data or canvas');
      return;
    }

    // Destroy existing chart
    if (chartRef.current) {
      chartRef.current.destroy();
      chartRef.current = null;
    }

    const ctx = canvasRef.current.getContext('2d');

    // Validate chart data structure (note: API transforms snake_case to camelCase)
    if (!memoizedChartData.data || !memoizedChartData.chartType) {
      console.error('ChartRenderer: Invalid chart data structure:', memoizedChartData);
      return;
    }

    console.log('ChartRenderer: Creating chart', { type: memoizedChartData.chartType, title: memoizedChartData.title });

    try {
      if (memoizedChartData.chartType === 'bar') {
        // Prepare data for bar chart
        const labels = memoizedChartData.data.labels || [];
        const values = memoizedChartData.data.values || memoizedChartData.data.datasets?.[0]?.data || [];

        chartRef.current = new Chart(ctx, {
          type: 'bar',
          data: {
            labels: labels,
            datasets: [{
              label: memoizedChartData.data.datasets?.[0]?.label || memoizedChartData.title || 'Data',
              data: values,
              backgroundColor: memoizedChartData.data.datasets?.[0]?.backgroundColor || [
                '#8B5CF6', '#A78BFA', '#C4B5FD', '#DDD6FE', '#EDE9FE',
                '#F3E8FF', '#7C3AED', '#5B21B6', '#4C1D95', '#3C1361'
              ],
              borderColor: '#6D28D9',
              borderWidth: 1
            }]
          },
          options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
              title: {
                display: true,
                text: memoizedChartData.title,
                color: '#E5E7EB',
                font: { size: 16, weight: 'bold' }
              },
              legend: {
                labels: { color: '#E5E7EB' }
              }
            },
            scales: {
              y: {
                beginAtZero: true,
                ticks: { color: '#9CA3AF' },
                grid: { color: '#374151' }
              },
              x: {
                ticks: { color: '#9CA3AF' },
                grid: { color: '#374151' }
              }
            }
          }
        });
      } else if (memoizedChartData.chartType === 'pie') {
        // Prepare data for pie chart
        const labels = memoizedChartData.data.labels || [];
        const values = memoizedChartData.data.values || memoizedChartData.data.datasets?.[0]?.data || [];

        chartRef.current = new Chart(ctx, {
          type: 'pie',
          data: {
            labels: labels,
            datasets: [{
              data: values,
              backgroundColor: memoizedChartData.data.datasets?.[0]?.backgroundColor || [
                '#8B5CF6', '#A78BFA', '#C4B5FD', '#DDD6FE', '#EDE9FE',
                '#F3E8FF', '#7C3AED', '#5B21B6', '#4C1D95', '#3C1361'
              ],
              borderColor: '#1F2937',
              borderWidth: 2
            }]
          },
          options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
              title: {
                display: true,
                text: memoizedChartData.title,
                color: '#E5E7EB',
                font: { size: 16, weight: 'bold' }
              },
              legend: {
                position: 'bottom',
                labels: { color: '#E5E7EB', padding: 20 }
              }
            }
          }
        });
      } else if (memoizedChartData.chartType === 'line') {
        // Prepare data for line chart
        const labels = memoizedChartData.data.labels || [];
        const values = memoizedChartData.data.values || memoizedChartData.data.datasets?.[0]?.data || [];

        chartRef.current = new Chart(ctx, {
          type: 'line',
          data: {
            labels: labels,
            datasets: [{
              label: memoizedChartData.data.datasets?.[0]?.label || memoizedChartData.title || 'Data',
              data: values,
              borderColor: '#8B5CF6',
              backgroundColor: 'rgba(139, 92, 246, 0.1)',
              tension: 0.4,
              fill: true,
              pointBackgroundColor: '#8B5CF6',
              pointBorderColor: '#6D28D9',
              pointRadius: 4
            }]
          },
          options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
              title: {
                display: true,
                text: memoizedChartData.title,
                color: '#E5E7EB',
                font: { size: 16, weight: 'bold' }
              },
              legend: {
                labels: { color: '#E5E7EB' }
              }
            },
            scales: {
              y: {
                beginAtZero: true,
                ticks: { color: '#9CA3AF' },
                grid: { color: '#374151' }
              },
              x: {
                ticks: { color: '#9CA3AF' },
                grid: { color: '#374151' }
              }
            }
          }
        });
      }
    } catch (error) {
      console.error('Error creating chart:', error);
    }

    // Cleanup function
    return () => {
      if (chartRef.current) {
        chartRef.current.destroy();
        chartRef.current = null;
      }
    };
  }, [memoizedChartData]);

  if (!memoizedChartData) return null;

  if (memoizedChartData.chartType === 'table') {
    return (
      <div className={`bg-gray-800 rounded-lg p-4 ${className}`}>
        <h3 className="text-lg font-semibold text-purple-200 mb-3">{memoizedChartData.title}</h3>
        <div className="overflow-x-auto">
          <table className="w-full text-sm text-gray-300">
            <thead>
              <tr className="border-b border-gray-600">
                {memoizedChartData.data.labels?.map((label, index) => (
                  <th key={index} className="text-left py-2 px-3 font-medium text-purple-300">
                    {label}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {memoizedChartData.data.values?.map((row, rowIndex) => (
                <tr key={rowIndex} className="border-b border-gray-700">
                  {Array.isArray(row) ? row.map((cell, cellIndex) => (
                    <td key={cellIndex} className="py-2 px-3">{cell}</td>
                  )) : (
                    <td className="py-2 px-3" colSpan={chartData.data.labels?.length || 1}>
                      {row}
                    </td>
                  )}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        {memoizedChartData.description && (
          <p className="text-sm text-gray-400 mt-3">{memoizedChartData.description}</p>
        )}
      </div>
    );
  }

  if (memoizedChartData.chartType === 'stats') {
    // Handle different stats data formats
    let statsData = memoizedChartData.data.stats || [];

    // If no stats array, create from labels and values
    if (statsData.length === 0 && memoizedChartData.data.labels && memoizedChartData.data.values) {
      statsData = memoizedChartData.data.labels.map((label, index) => ({
        label: label,
        value: memoizedChartData.data.values[index] || 0
      }));
    }

    return (
      <div className={`bg-gray-800 rounded-lg p-4 ${className}`}>
        <h3 className="text-lg font-semibold text-purple-200 mb-3">{memoizedChartData.title}</h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {statsData.map((stat, index) => (
            <div key={index} className="bg-gray-700 rounded-lg p-3 text-center">
              <div className="text-2xl font-bold text-purple-300">{stat.value}</div>
              <div className="text-sm text-gray-400">{stat.label}</div>
            </div>
          ))}
        </div>
        {memoizedChartData.description && (
          <p className="text-sm text-gray-400 mt-3">{memoizedChartData.description}</p>
        )}
      </div>
    );
  }

  return (
    <div className={`bg-gray-800 rounded-lg p-4 ${className}`}>
      <div className="h-64 md:h-80">
        <canvas ref={canvasRef}></canvas>
      </div>
      {memoizedChartData.description && (
        <p className="text-sm text-gray-400 mt-3">{memoizedChartData.description}</p>
      )}
    </div>
  );
};

export default ChartRenderer;
