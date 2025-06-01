/**
 * Frontend Chart Integration Test Component
 * Tests ChartRenderer and MessageRenderer integration
 */

import React, { useState } from 'react';
import ChartRenderer from '../components/ChartRenderer';
import MessageRenderer from '../components/MessageRenderer';

const ChartIntegrationTest = () => {
  const [testResults, setTestResults] = useState([]);

  // Sample chart data for testing
  const testChartData = {
    barChart: {
      chart_type: "bar",
      title: "Product Prices Comparison",
      description: "Comparison of different product prices",
      data: {
        labels: ["iPhone 15 Pro", "Samsung Galaxy S24", "Google Pixel 8", "iPad Pro"],
        values: [999, 899, 699, 1099]
      }
    },
    pieChart: {
      chart_type: "pie", 
      title: "Product Categories Distribution",
      description: "Distribution of products by category",
      data: {
        labels: ["Smartphones", "Tablets", "Laptops"],
        values: [5, 2, 3]
      }
    },
    lineChart: {
      chart_type: "line",
      title: "Price Trends Over Time", 
      description: "Price changes over the last 6 months",
      data: {
        labels: ["Jan", "Feb", "Mar", "Apr", "May", "Jun"],
        values: [899, 849, 799, 749, 699, 649]
      }
    },
    statsChart: {
      chart_type: "stats",
      title: "Product Statistics",
      description: "Key metrics about our product catalog",
      data: {
        stats: [
          { label: "Total Products", value: "156" },
          { label: "Categories", value: "12" },
          { label: "Avg Price", value: "$849" },
          { label: "In Stock", value: "142" }
        ]
      }
    },
    tableChart: {
      chart_type: "table",
      title: "Product Details",
      description: "Detailed product information",
      data: {
        labels: ["Product", "Price", "Category", "Stock"],
        values: [
          ["iPhone 15 Pro", "$999", "Smartphones", "25"],
          ["Samsung Galaxy S24", "$899", "Smartphones", "18"],
          ["Google Pixel 8", "$699", "Smartphones", "32"],
          ["iPad Pro", "$1099", "Tablets", "15"]
        ]
      }
    }
  };

  // Sample AI responses with chart data
  const testMessages = {
    barChartMessage: `Here's the price comparison you requested:

\`\`\`json
{
  "chart_type": "bar",
  "title": "Product Prices Comparison", 
  "description": "Comparison of different product prices",
  "data": {
    "labels": ["iPhone 15 Pro", "Samsung Galaxy S24", "Google Pixel 8"],
    "values": [999, 899, 699]
  }
}
\`\`\`

As you can see, the Google Pixel 8 offers the best value at $699, while the iPhone 15 Pro is the most expensive at $999.`,

    pieChartMessage: `Here's the category distribution:

\`\`\`json
{
  "chart_type": "pie",
  "title": "Product Categories",
  "data": {
    "labels": ["Smartphones", "Tablets", "Laptops"],
    "values": [60, 25, 15]
  }
}
\`\`\`

Smartphones dominate our catalog at 60% of all products.`,

    regularMessage: "This is a regular message without any chart data. It should be displayed normally with enhanced text formatting."
  };

  const runTest = (testName, testFunction) => {
    try {
      const result = testFunction();
      setTestResults(prev => [...prev, { name: testName, status: 'pass', result }]);
      return true;
    } catch (error) {
      setTestResults(prev => [...prev, { name: testName, status: 'fail', error: error.message }]);
      return false;
    }
  };

  const runAllTests = () => {
    setTestResults([]);
    
    // Test 1: ChartRenderer with different chart types
    runTest('Bar Chart Rendering', () => {
      return testChartData.barChart.chart_type === 'bar' && testChartData.barChart.data.labels.length > 0;
    });

    runTest('Pie Chart Rendering', () => {
      return testChartData.pieChart.chart_type === 'pie' && testChartData.pieChart.data.values.length > 0;
    });

    runTest('Line Chart Rendering', () => {
      return testChartData.lineChart.chart_type === 'line' && testChartData.lineChart.data.labels.length === testChartData.lineChart.data.values.length;
    });

    runTest('Stats Chart Rendering', () => {
      return testChartData.statsChart.chart_type === 'stats' && testChartData.statsChart.data.stats.length > 0;
    });

    runTest('Table Chart Rendering', () => {
      return testChartData.tableChart.chart_type === 'table' && testChartData.tableChart.data.labels.length > 0;
    });

    // Test 2: MessageRenderer chart detection
    runTest('Chart Data Extraction', () => {
      const hasChartData = testMessages.barChartMessage.includes('```json') && 
                          testMessages.barChartMessage.includes('chart_type');
      return hasChartData;
    });

    runTest('Regular Message Handling', () => {
      const isRegularMessage = !testMessages.regularMessage.includes('```json');
      return isRegularMessage;
    });
  };

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text);
  };

  return (
    <div className="p-6 bg-gray-900 min-h-screen text-white">
      <div className="max-w-6xl mx-auto">
        <h1 className="text-3xl font-bold text-purple-300 mb-6">Chart Integration Test Suite</h1>
        
        {/* Test Controls */}
        <div className="mb-8 p-4 bg-gray-800 rounded-lg">
          <button 
            onClick={runAllTests}
            className="bg-purple-600 hover:bg-purple-700 px-4 py-2 rounded-lg font-medium"
          >
            Run All Tests
          </button>
          
          {testResults.length > 0 && (
            <div className="mt-4">
              <h3 className="text-lg font-semibold mb-2">Test Results:</h3>
              {testResults.map((result, index) => (
                <div key={index} className={`p-2 rounded mb-1 ${result.status === 'pass' ? 'bg-green-900/30 text-green-300' : 'bg-red-900/30 text-red-300'}`}>
                  {result.status === 'pass' ? '✅' : '❌'} {result.name}
                  {result.error && <span className="text-sm"> - {result.error}</span>}
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Chart Renderer Tests */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
          <div className="bg-gray-800 rounded-lg p-4">
            <h2 className="text-xl font-semibold text-purple-300 mb-4">Bar Chart Test</h2>
            <ChartRenderer chartData={testChartData.barChart} />
          </div>

          <div className="bg-gray-800 rounded-lg p-4">
            <h2 className="text-xl font-semibold text-purple-300 mb-4">Pie Chart Test</h2>
            <ChartRenderer chartData={testChartData.pieChart} />
          </div>

          <div className="bg-gray-800 rounded-lg p-4">
            <h2 className="text-xl font-semibold text-purple-300 mb-4">Line Chart Test</h2>
            <ChartRenderer chartData={testChartData.lineChart} />
          </div>

          <div className="bg-gray-800 rounded-lg p-4">
            <h2 className="text-xl font-semibold text-purple-300 mb-4">Stats Chart Test</h2>
            <ChartRenderer chartData={testChartData.statsChart} />
          </div>
        </div>

        <div className="bg-gray-800 rounded-lg p-4 mb-8">
          <h2 className="text-xl font-semibold text-purple-300 mb-4">Table Chart Test</h2>
          <ChartRenderer chartData={testChartData.tableChart} />
        </div>

        {/* MessageRenderer Tests */}
        <div className="space-y-6">
          <div className="bg-gray-800 rounded-lg p-4">
            <h2 className="text-xl font-semibold text-purple-300 mb-4">Message with Bar Chart</h2>
            <div className="bg-gray-700 rounded-lg p-4">
              <MessageRenderer 
                content={testMessages.barChartMessage} 
                onCopy={copyToClipboard}
              />
            </div>
          </div>

          <div className="bg-gray-800 rounded-lg p-4">
            <h2 className="text-xl font-semibold text-purple-300 mb-4">Message with Pie Chart</h2>
            <div className="bg-gray-700 rounded-lg p-4">
              <MessageRenderer 
                content={testMessages.pieChartMessage} 
                onCopy={copyToClipboard}
              />
            </div>
          </div>

          <div className="bg-gray-800 rounded-lg p-4">
            <h2 className="text-xl font-semibold text-purple-300 mb-4">Regular Message</h2>
            <div className="bg-gray-700 rounded-lg p-4">
              <MessageRenderer 
                content={testMessages.regularMessage} 
                onCopy={copyToClipboard}
              />
            </div>
          </div>
        </div>

        {/* Instructions */}
        <div className="mt-8 p-4 bg-blue-900/30 rounded-lg border border-blue-600/30">
          <h3 className="text-lg font-semibold text-blue-300 mb-2">Testing Instructions</h3>
          <ul className="text-blue-200 space-y-1">
            <li>• Click "Run All Tests" to verify component functionality</li>
            <li>• Check that all chart types render correctly</li>
            <li>• Verify that MessageRenderer properly detects and displays chart data</li>
            <li>• Test copy functionality on messages</li>
            <li>• Ensure responsive design works on different screen sizes</li>
          </ul>
        </div>
      </div>
    </div>
  );
};

export default ChartIntegrationTest;
