import React, { useState } from 'react';
import ChartRenderer from './ChartRenderer';

const ChartTest = () => {
  // Mock chart data that matches the expected format
  const mockChartData = {
    chartType: 'bar',
    title: 'Sales by Region',
    data: {
      labels: ['North', 'South', 'East', 'West'],
      values: [12, 19, 3, 5],
      datasets: [
        {
          label: 'Sales',
          data: [12, 19, 3, 5],
          backgroundColor: [
            'rgba(255, 99, 132, 0.5)',
            'rgba(54, 162, 235, 0.5)',
            'rgba(255, 206, 86, 0.5)',
            'rgba(75, 192, 192, 0.5)',
          ],
          borderColor: [
            'rgba(255, 99, 132, 1)',
            'rgba(54, 162, 235, 1)',
            'rgba(255, 206, 86, 1)',
            'rgba(75, 192, 192, 1)',
          ],
          borderWidth: 1,
        },
      ],
    },
  };

  // Also test with snake_case format
  const mockChartDataSnakeCase = {
    chart_type: 'bar',
    title: 'Sales by Region (Snake Case)',
    data: {
      labels: ['North', 'South', 'East', 'West'],
      values: [8, 15, 10, 7],
      datasets: [
        {
          label: 'Sales',
          data: [8, 15, 10, 7],
          backgroundColor: [
            'rgba(153, 102, 255, 0.5)',
            'rgba(255, 159, 64, 0.5)',
            'rgba(255, 99, 71, 0.5)',
            'rgba(75, 192, 192, 0.5)',
          ],
          borderColor: [
            'rgba(153, 102, 255, 1)',
            'rgba(255, 159, 64, 1)',
            'rgba(255, 99, 71, 1)',
            'rgba(75, 192, 192, 1)',
          ],
          borderWidth: 1,
        },
      ],
    },
  };

  const [activeTab, setActiveTab] = useState('camel');

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <h1 className="text-2xl font-bold mb-6 text-white">Chart Rendering Test</h1>
      
      <div className="mb-6">
        <div className="flex border-b border-gray-700 mb-4">
          <button
            className={`py-2 px-4 font-medium ${
              activeTab === 'camel'
                ? 'text-purple-400 border-b-2 border-purple-400'
                : 'text-gray-400 hover:text-white'
            }`}
            onClick={() => setActiveTab('camel')}
          >
            CamelCase Format
          </button>
          <button
            className={`py-2 px-4 font-medium ${
              activeTab === 'snake'
                ? 'text-purple-400 border-b-2 border-purple-400'
                : 'text-gray-400 hover:text-white'
            }`}
            onClick={() => setActiveTab('snake')}
          >
            Snake Case Format
          </button>
        </div>

        <div className="bg-gray-800 rounded-lg p-6">
          {activeTab === 'camel' ? (
            <>
              <h2 className="text-xl font-semibold mb-4 text-white">CamelCase Format</h2>
              <div className="h-96">
                <ChartRenderer chartData={mockChartData} />
              </div>
              <div className="mt-4 p-4 bg-gray-900 rounded">
                <pre className="text-xs text-gray-300 overflow-auto">
                  {JSON.stringify(mockChartData, null, 2)}
                </pre>
              </div>
            </>
          ) : (
            <>
              <h2 className="text-xl font-semibold mb-4 text-white">Snake Case Format</h2>
              <div className="h-96">
                <ChartRenderer chartData={mockChartDataSnakeCase} />
              </div>
              <div className="mt-4 p-4 bg-gray-900 rounded">
                <pre className="text-xs text-gray-300 overflow-auto">
                  {JSON.stringify(mockChartDataSnakeCase, null, 2)}
                </pre>
              </div>
            </>
          )}
        </div>
      </div>

      <div className="mt-8 p-4 bg-gray-800 rounded-lg">
        <h2 className="text-lg font-semibold mb-2 text-white">Test Results</h2>
        <p className="text-gray-300">
          Check the browser console for any errors or warnings related to chart rendering.
        </p>
      </div>
    </div>
  );
};

export default ChartTest;
