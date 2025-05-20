import { useState } from 'react';
import { Globe, Trash2, Clock, Eye, FileText, Book, Download, RefreshCw, Database } from 'lucide-react';

const formatDate = (dateString) => {
  if (!dateString) return 'Invalid Date';
  const date = new Date(dateString);
  return new Intl.DateTimeFormat('en-US', {
    year: 'numeric', month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit'
  }).format(date);
};

function HistoryPanel({ scrapingHistory, projectName, onDeleteHistoryItem }) {
  const [selectedHistoryItem, setSelectedHistoryItem] = useState(null);

  const viewHistoryDetail = (item) => {
    setSelectedHistoryItem(item);
  };

  const closeHistoryDetail = () => {
    setSelectedHistoryItem(null);
  };

  return (
    <div className="flex-1 p-4 overflow-auto">
      <div className="mb-6">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-xl font-semibold text-purple-200">
            Scraping History: <span className="text-indigo-300">{projectName}</span>
          </h2>
        </div>

        {selectedHistoryItem ? (
          <div className="bg-purple-800 bg-opacity-60 p-5 rounded-lg shadow-lg border border-purple-700 mb-4">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-lg font-medium text-purple-200">
                History Detail
              </h3>
              <button
                onClick={closeHistoryDetail}
                className="p-2 hover:bg-purple-700 rounded-md text-purple-300"
              >
                Back to list
              </button>
            </div>

            <div className="space-y-4">
              <div className="flex items-start space-x-2">
                <Globe className="text-purple-300 mt-1" size={18} />
                <div>
                  <span className="font-medium text-purple-200">URL(s):</span>
                  <p className="text-purple-300 break-all">{selectedHistoryItem.url}</p>
                </div>
              </div>

              <div className="flex items-center space-x-2">
                <Clock className="text-purple-300" size={18} />
                <span className="font-medium text-purple-200">Timestamp:</span>
                <span className="text-purple-300">{formatDate(selectedHistoryItem.timestamp)}</span>
              </div>

              <div className="flex items-center space-x-2">
                <Database className="text-purple-300" size={18} />
                <span className="font-medium text-purple-200">Data Size:</span>
                <span className="text-purple-300">{selectedHistoryItem.dataSize}</span>
              </div>

              <div className="flex items-center space-x-2">
                <FileText className="text-purple-300" size={18} />
                <span className="font-medium text-purple-200">Items Scraped:</span>
                <span className="text-purple-300">{selectedHistoryItem.itemsScraped}</span>
              </div>

              <div className="flex items-center space-x-2">
                <span className="font-medium text-purple-200">Status:</span>
                <span className={`px-2 py-1 rounded-full text-xs ${
                  selectedHistoryItem.status === 'completed'
                    ? 'bg-green-800 text-green-200'
                    : 'bg-red-800 text-red-200'
                }`}>
                  {selectedHistoryItem.status}
                </span>
              </div>

              <div className="mt-6">
                <h4 className="font-medium text-purple-200 mb-2 flex items-center">
                  <Book className="mr-2" size={16} />
                  Sample Data (Mock)
                </h4>
                <div className="bg-purple-900 bg-opacity-50 p-3 rounded-md border border-purple-700 max-h-40 overflow-y-auto">
                  {selectedHistoryItem.status === 'completed' ? (
                    <pre className="text-xs text-purple-300 whitespace-pre-wrap">
                      {`{
  "results": [
    { "title": "Sample Item 1", "price": "$29.99", "rating": 4.5 },
    { "title": "Sample Item 2", "price": "$19.99", "rating": 3.8 }
  ],
  "metadata": {
    "source_project": "${projectName}",
    "scraped_urls": "${selectedHistoryItem.url}",
    "timestamp": "${selectedHistoryItem.timestamp}"
  }
}`}
                    </pre>
                  ) : (
                    <div className="text-red-300 text-sm">
                      Error retrieving data. The scraping operation may have failed.
                    </div>
                  )}
                </div>
              </div>

              <div className="flex space-x-3 mt-4">
                <button className="flex items-center space-x-2 px-4 py-2 bg-purple-700 hover:bg-purple-600 rounded-md" title="Download (Not Implemented)">
                  <Download size={16} />
                  <span>Download Data</span>
                </button>

                <button className="flex items-center space-x-2 px-4 py-2 bg-indigo-600 hover:bg-indigo-500 rounded-md" title="Repeat Scrape (Not Implemented)">
                  <RefreshCw size={16} />
                  <span>Repeat Scrape</span>
                </button>
              </div>
            </div>
          </div>
        ) : (
          // History List
          scrapingHistory && scrapingHistory.length > 0 ? (
            <div className="space-y-4">
              {scrapingHistory.map(item => (
                <div key={item.id} className="bg-purple-800 bg-opacity-40 p-4 rounded-lg shadow-md border border-purple-700 flex justify-between items-center">
                  <div className="flex-1 overflow-hidden mr-2">
                    <div className="font-medium text-purple-200 truncate" title={item.url}>{item.url}</div>
                    <div className="text-sm text-purple-300">
                      {formatDate(item.timestamp)} • {item.dataSize} • {item.itemsScraped} items
                    </div>
                    <div className="mt-1">
                      <span className={`text-xs px-2 py-1 rounded-full ${
                        item.status === 'completed' ? 'bg-green-800 text-green-200' : 'bg-red-800 text-red-200'
                      }`}>
                        {item.status}
                      </span>
                    </div>
                  </div>
                  <div className="flex space-x-2 flex-shrink-0">
                    <button
                      onClick={() => viewHistoryDetail(item)}
                      className="p-2 text-purple-300 hover:text-purple-100"
                      title="View details"
                    >
                      <Eye size={16} />
                    </button>
                    <button className="p-2 text-purple-300 hover:text-purple-100" title="Download data (Not Implemented)">
                      <Download size={16} />
                    </button>
                    <button
                      onClick={() => onDeleteHistoryItem(item.id)}
                      className="p-2 text-purple-300 hover:text-red-400"
                      title="Delete from history"
                    >
                      <Trash2 size={16} />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          ) : (
             <div className="bg-purple-800 bg-opacity-30 p-8 rounded-lg text-center border border-purple-700">
                <Clock size={40} className="mx-auto text-purple-400 mb-4" />
                <p className="text-purple-300">No scraping history yet for project "{projectName}".</p>
            </div>
          )
        )}
      </div>
    </div>
  );
}

export default HistoryPanel;