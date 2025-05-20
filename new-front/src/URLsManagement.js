import { useState } from 'react';
import { Globe, PlusCircle, PlayCircle, XCircle, Database, AlertCircle, ChevronLeft, ChevronRight, ToggleLeft, ToggleRight } from 'lucide-react';

function URLManagementPanel({
  urls,
  onAddUrl,
  onRemoveAllUrls,
  onStartScraping,
  onDeleteUrl,
  onDeleteScrapingResult,
  scrapingResults,
  isScrapingError,
  errorMessage,
  projectName,
}) {
  const [newUrl, setNewUrl] = useState('');
  const [newCondition, setNewCondition] = useState('');
  const [displayFormat, setDisplayFormat] = useState('table');

  const [currentPage, setCurrentPage] = useState(1);
  const [itemsPerPage] = useState(4);
  const [paginationEnabled, setPaginationEnabled] = useState(true);

  const isAddButtonDisabled = !newUrl.trim() || !newCondition.trim();

  const handleAddClick = () => {
    if (newUrl.trim() && newCondition.trim()) {
        onAddUrl({
          url: newUrl,
          conditions: newCondition,
          display_format: displayFormat
        });
        setNewUrl('');
        setNewCondition('');
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !isAddButtonDisabled) {
      handleAddClick();
    }
  };

  const togglePagination = () => {
    setPaginationEnabled(!paginationEnabled);
    if (!paginationEnabled) {
      setCurrentPage(1);
    }
  };

  const startIndex = (currentPage - 1) * itemsPerPage;
  const endIndex = startIndex + itemsPerPage;
  const displayedUrls = paginationEnabled && urls
    ? urls.slice(startIndex, endIndex)
    : urls;

  const totalPages = urls ? Math.ceil(urls.length / itemsPerPage) : 1;

  const paginate = (pageNumber) => {
    if (pageNumber > 0 && pageNumber <= totalPages) {
      setCurrentPage(pageNumber);
    }
  };

  if (currentPage > totalPages && totalPages > 0) {
    setCurrentPage(totalPages);
  } else if (urls && urls.length === 0 && currentPage !== 1) {
    setCurrentPage(1);
  }

  const downloadAsCSV = (data, filename, tabularData = null, fields = null, displayFormat = 'table') => {
    let csvContent;

    if (tabularData && tabularData.length > 0 && fields && fields.length > 0) {
      // Use tabular data if available
      if (displayFormat === 'table') {
        // Table format - each row is a CSV row
        csvContent =
          "data:text/csv;charset=utf-8," +
          [fields.join(","), ...tabularData.map(row =>
            fields.map(field => {
              // Escape commas and quotes in the value
              const value = row[field] || "";
              const escapedValue = value.toString().replace(/"/g, '""');
              return `"${escapedValue}"`;
            }).join(",")
          )].join("\n");
      } else {
        // Paragraph or raw format - each item is a separate section
        const rows = [];
        rows.push("Item,Field,Value");

        tabularData.forEach((row, rowIndex) => {
          fields.forEach(field => {
            const value = row[field] || "";
            const escapedValue = value.toString().replace(/"/g, '""');
            rows.push(`"Item ${rowIndex + 1}","${field}","${escapedValue}"`);
          });
        });

        csvContent = "data:text/csv;charset=utf-8," + rows.join("\n");
      }
    } else {
      // Fallback to the old format
      csvContent =
        "data:text/csv;charset=utf-8," +
        ["Title,Value", ...data.map(item => {
          const title = item.title.replace(/"/g, '""');
          const value = (item.value || "").toString().replace(/"/g, '""');
          return `"${title}","${value}"`;
        })].join("\n");
    }

    const encodedUri = encodeURI(csvContent);
    const link = document.createElement("a");
    link.setAttribute("href", encodedUri);
    link.setAttribute("download", filename);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const downloadAsJSON = (data, filename, tabularData = null, displayFormat = 'table') => {
    let jsonData;

    if (tabularData && tabularData.length > 0) {
      if (displayFormat === 'table') {
        // Table format - use tabular data as is
        jsonData = tabularData;
      } else if (displayFormat === 'paragraph') {
        // Paragraph format - structure data by items
        jsonData = {
          items: tabularData.map((row, index) => {
            return {
              item_number: index + 1,
              fields: Object.entries(row).map(([field, value]) => ({
                field,
                value: value || ""
              }))
            };
          })
        };
      } else {
        // Raw format - flatten the data
        jsonData = {
          raw_data: tabularData.map((row, index) => {
            return {
              item_number: index + 1,
              ...row
            };
          })
        };
      }
    } else {
      // Fallback to the old format
      jsonData = data.reduce((obj, item) => {
        obj[item.title] = item.value;
        return obj;
      }, {});
    }

    const jsonStr = JSON.stringify(jsonData, null, 2);
    const blob = new Blob([jsonStr], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <div className="flex-1 p-4 overflow-auto">
      <div className="mb-6">
         <div className="flex justify-between items-center mb-4">
          <h2 className="text-xl font-semibold text-purple-200">
            URL Management: <span className="text-indigo-300">{projectName}</span>
          </h2>
          <div className="flex items-center space-x-2 bg-purple-800 bg-opacity-60 p-2 rounded-lg">
            <span className="text-sm">Pagination:</span>
            <button onClick={togglePagination} className="hover:bg-purple-700 p-1 rounded">
              {paginationEnabled ? (
                <ToggleRight size={22} className="text-green-400" />
              ) : (
                <ToggleLeft size={22} className="text-purple-400" />
              )}
            </button>
          </div>
        </div>

        <div className="bg-purple-800 bg-opacity-60 p-4 rounded-lg shadow-lg mb-6 border border-purple-700">
          <h3 className="text-lg font-medium mb-3 text-purple-200">Add New URL</h3>
          <div className="space-y-3">
            <div>
              <label htmlFor="new-url-input" className="block text-purple-300 text-sm mb-1">URL <span className="text-red-400">*</span></label>
              <input
                id="new-url-input"
                type="url"
                value={newUrl}
                onChange={(e) => setNewUrl(e.target.value)}
                placeholder="https://example.com"
                className="w-full p-2 rounded-md bg-purple-700 border border-purple-600 text-white placeholder-purple-400 focus:outline-none focus:ring-2 focus:ring-purple-400"
                required
              />
            </div>
            <div>
              <label htmlFor="new-condition-input" className="block text-purple-300 text-sm mb-1">Scraping Conditions <span className="text-red-400">*</span></label>
              <input
                id="new-condition-input"
                type="text"
                value={newCondition}
                onChange={(e) => setNewCondition(e.target.value)}
                placeholder="e.g., title, price, description"
                className="w-full p-2 rounded-md bg-purple-700 border border-purple-600 text-white placeholder-purple-400 focus:outline-none focus:ring-2 focus:ring-purple-400"
                onKeyDown={handleKeyPress}
                required
              />
            </div>
            <div>
              <label htmlFor="display-format-select" className="block text-purple-300 text-sm mb-1">Display Format</label>
              <select
                id="display-format-select"
                value={displayFormat}
                onChange={(e) => setDisplayFormat(e.target.value)}
                className="w-full p-2 rounded-md bg-purple-700 border border-purple-600 text-white focus:outline-none focus:ring-2 focus:ring-purple-400"
              >
                <option value="table">Table View</option>
                <option value="paragraph">Paragraph View</option>
                <option value="raw">Raw View</option>
              </select>
            </div>
            <div className="flex space-x-3 pt-2">
              <button
                onClick={handleAddClick}
                className={`flex items-center space-x-2 px-4 py-2 rounded-md transition-colors ${
                  isAddButtonDisabled
                    ? 'bg-purple-800 text-purple-400 cursor-not-allowed'
                    : 'bg-purple-600 hover:bg-purple-500 text-white'
                }`}
                disabled={isAddButtonDisabled}
              >
                <PlusCircle size={16} />
                <span>Add URL</span>
              </button>

               <button
                onClick={onRemoveAllUrls}
                className={`flex items-center space-x-2 px-4 py-2 rounded-md transition-colors ${
                    !urls || urls.length === 0
                    ? 'bg-purple-900 text-purple-500 cursor-not-allowed'
                    : 'bg-red-700 hover:bg-red-600 text-white'
                }`}
                disabled={!urls || urls.length === 0}
              >
                <XCircle size={16} />
                <span>Remove All URLs</span>
              </button>

              <button
                onClick={onStartScraping}
                className={`flex items-center space-x-2 px-4 py-2 rounded-md transition-colors ${
                    !urls || urls.length === 0
                    ? 'bg-purple-900 text-purple-500 cursor-not-allowed'
                    : 'bg-violet-600 hover:bg-violet-500 text-white'
                }`}
                disabled={!urls || urls.length === 0}
              >
                <PlayCircle size={16} />
                <span>Scrape</span>
              </button>
            </div>
             {isAddButtonDisabled && (newUrl.length > 0 || newCondition.length > 0) && (
                <p className="text-xs text-yellow-400 mt-2">Please fill in both URL and Scraping Conditions.</p>
            )}
          </div>
        </div>

        {isScrapingError && (
          <div className="bg-red-900 bg-opacity-50 p-4 rounded-lg border border-red-700 mb-6">
            <div className="flex items-center text-red-300">
              <AlertCircle className="mr-2" size={20} />
              <span>{errorMessage}</span>
            </div>
          </div>
        )}

        {scrapingResults && (
          <div className="bg-indigo-900 bg-opacity-40 p-4 rounded-lg border border-indigo-700 mb-6">
            <h3 className="text-lg font-medium mb-3 text-indigo-200 flex items-center">
              <Database className="mr-2" size={18} />
              Scraping Results
            </h3>
            <div className="space-y-4">
              {scrapingResults.map((result, resultIndex) => {
                const conditionsArray = result.conditions.split(',').map(c => c.trim());
                return (
                  <div key={resultIndex} className="bg-indigo-800 bg-opacity-50 p-3 rounded-lg border border-indigo-700">
                    <div className="flex justify-between items-start mb-2">
                      <div className="font-medium text-indigo-200 break-all mr-2">{result.url}</div>
                      <button
                        onClick={() => onDeleteScrapingResult && onDeleteScrapingResult(resultIndex)}
                        className="p-1 text-indigo-300 hover:text-red-400 hover:bg-indigo-700 rounded-md transition-colors flex-shrink-0"
                        title="Delete Result"
                      >
                        <XCircle size={18} />
                      </button>
                    </div>
                    <div className="text-sm text-indigo-300 mb-2">Conditions: {result.conditions}</div>
                    <div className="bg-indigo-900 p-2 rounded-md overflow-x-auto">
                      {/* Display format selector */}
                      <div className="flex justify-end mb-2">
                        <select
                          value={result.display_format || 'table'}
                          onChange={(e) => {
                            // Update the display format for this result
                            const updatedResults = [...scrapingResults];
                            updatedResults[resultIndex].display_format = e.target.value;
                            // This would normally update the state in the parent component
                            // For now, we'll just update the UI
                            document.getElementById(`display-format-${resultIndex}`).setAttribute('data-format', e.target.value);
                          }}
                          className="bg-indigo-800 border border-indigo-600 text-indigo-200 text-sm rounded-md p-1"
                          id={`display-format-${resultIndex}`}
                          data-format={result.display_format || 'table'}
                        >
                          <option value="table">Table View</option>
                          <option value="paragraph">Paragraph View</option>
                          <option value="raw">Raw View</option>
                        </select>
                      </div>

                      {/* Table View */}
                      {(result.display_format === 'table' || !result.display_format) && result.tabularData && result.tabularData.length > 0 && (
                        <table className="w-full text-sm">
                          <thead>
                            <tr className="text-indigo-300 border-b border-indigo-700">
                              <th className="text-left py-1 px-2">#</th>
                              {result.fields.map((field, idx) => (
                                <th key={idx} className="text-left py-1 px-2">{field}</th>
                              ))}
                            </tr>
                          </thead>
                          <tbody>
                            {result.tabularData.map((row, rowIdx) => (
                              <tr key={rowIdx} className="border-b border-indigo-800 text-indigo-200">
                                <td className="py-1 px-2">{rowIdx + 1}</td>
                                {result.fields.map((field, colIdx) => (
                                  <td key={colIdx} className="py-1 px-2">{row[field] || ''}</td>
                                ))}
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      )}

                      {/* Paragraph View */}
                      {result.display_format === 'paragraph' && result.formatted_data && result.formatted_data.paragraph_data && (
                        <div className="text-indigo-200 whitespace-pre-wrap font-mono text-sm p-2">
                          {result.formatted_data.paragraph_data}
                        </div>
                      )}

                      {/* Raw View */}
                      {result.display_format === 'raw' && result.formatted_data && result.formatted_data.raw_data && (
                        <div className="text-indigo-200 whitespace-pre-wrap font-mono text-sm p-2 bg-indigo-950 rounded">
                          {result.formatted_data.raw_data}
                        </div>
                      )}

                      {/* Fallback to the old display method if no tabular data */}
                      {(!result.tabularData || result.tabularData.length === 0) && (
                        <table className="w-full text-sm">
                          <thead>
                            <tr className="text-indigo-300 border-b border-indigo-700">
                              <th className="text-left py-1 px-2">Field</th>
                              <th className="text-left py-1 px-2">Value</th>
                            </tr>
                          </thead>
                          <tbody>
                            {result.results.map((item, idx) => (
                              <tr key={idx} className="border-b border-indigo-800 text-indigo-200">
                                <td className="py-1 px-2 font-medium">{item.title}</td>
                                <td className="py-1 px-2">{item.value}</td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      )}
                      <div className="flex flex-wrap gap-2 mt-3">
                        <button
                          onClick={() => downloadAsCSV(
                            result.results,
                            `scraping_${result.url.replace(/[^a-zA-Z0-9]/g, '_')}_${resultIndex + 1}.csv`,
                            result.tabularData,
                            result.fields,
                            result.display_format
                          )}
                          className="bg-purple-600 hover:bg-purple-500 text-white px-3 py-1 rounded-md text-sm">
                          Download CSV
                        </button>
                        <button
                          onClick={() => downloadAsJSON(
                            result.results,
                            `scraping_${result.url.replace(/[^a-zA-Z0-9]/g, '_')}_${resultIndex + 1}.json`,
                            result.tabularData,
                            result.display_format
                          )}
                          className="bg-purple-600 hover:bg-purple-500 text-white px-3 py-1 rounded-md text-sm">
                          Download JSON
                        </button>
                        <button
                          onClick={() => {
                            // Download PDF (actually HTML that can be printed to PDF)
                            const pdfUrl = `http://localhost:8000/download/${result.project_id}/${result.session_id}/pdf`;
                            window.open(pdfUrl, '_blank');
                          }}
                          className="bg-purple-600 hover:bg-purple-500 text-white px-3 py-1 rounded-md text-sm">
                          Download PDF
                        </button>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {urls && urls.length > 0 && (
          <>
            <h3 className="text-lg font-medium mb-3 text-purple-200">URL List ({urls.length} total)</h3>
            <div className="space-y-4 mb-6">
              {displayedUrls.map(url => (
                <div key={url.id} className="bg-purple-800 bg-opacity-40 p-4 rounded-lg shadow-md border border-purple-700 flex justify-between items-center">
                  <div className="flex-1 min-w-0">
                     <div className="font-medium text-purple-200 truncate" title={url.url}>{url.url}</div>
                     <div className="text-sm text-purple-300 truncate" title={url.conditions}>Conditions: {url.conditions}</div>
                    <div className="mt-1">
                      <span className={`text-xs px-2 py-1 rounded-full ${
                        url.status === 'pending' ? 'bg-yellow-800 text-yellow-200' :
                        url.status === 'completed' ? 'bg-green-800 text-green-200' :
                        'bg-red-800 text-red-200'
                      }`}>
                        {url.status}
                      </span>
                    </div>
                  </div>
                  <div className="flex items-center ml-4">
                    <button
                      onClick={() => {
                        console.log("Deleting URL with ID:", url.id);
                        onDeleteUrl && onDeleteUrl(url.id);
                      }}
                      className="p-2 text-purple-300 hover:text-red-400 hover:bg-purple-700 rounded-md transition-colors"
                      title="Delete URL"
                      data-url-id={url.id}
                    >
                      <XCircle size={18} />
                    </button>
                  </div>
                </div>
              ))}
            </div>

            {paginationEnabled && urls.length > itemsPerPage && (
              <div className="flex justify-center mt-6 space-x-2">
                <button
                  onClick={() => paginate(currentPage - 1)}
                  disabled={currentPage === 1}
                  className={`p-2 rounded-md ${
                    currentPage === 1
                      ? 'bg-purple-800 text-purple-500 cursor-not-allowed'
                      : 'bg-purple-700 hover:bg-purple-600 text-white'
                  }`}
                >
                  <ChevronLeft size={16} />
                </button>
                <div className="flex items-center px-3 bg-purple-800 bg-opacity-60 rounded-md">
                  <span>Page {currentPage} of {totalPages}</span>
                </div>
                <button
                  onClick={() => paginate(currentPage + 1)}
                  disabled={currentPage === totalPages}
                  className={`p-2 rounded-md ${
                    currentPage === totalPages
                      ? 'bg-purple-800 text-purple-500 cursor-not-allowed'
                      : 'bg-purple-700 hover:bg-purple-600 text-white'
                  }`}
                >
                  <ChevronRight size={16} />
                </button>
              </div>
            )}
          </>
        )}

        {(!urls || urls.length === 0) && !isScrapingError && !scrapingResults && (
          <div className="bg-purple-800 bg-opacity-30 p-8 rounded-lg text-center border border-purple-700">
            <Globe size={40} className="mx-auto text-purple-400 mb-4" />
            <p className="text-purple-300">No URLs added to project "{projectName}" yet.</p>
            <p className="text-purple-400">Add URLs with scraping conditions above to begin.</p>
          </div>
        )}
      </div>
    </div>
  );
}

export default URLManagementPanel;