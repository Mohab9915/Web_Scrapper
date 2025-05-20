import React, { useState } from 'react';
import ForceRefreshToggle from './ForceRefreshToggle';
import { executeScrape } from '../lib/api';
import './styles.css';

/**
 * Modal component for interactive scraping with force refresh option
 *
 * @param {Object} props - Component props
 * @param {string} props.projectId - The ID of the current project
 * @param {string} props.url - The URL to scrape
 * @param {string} props.sessionId - The session ID for the scraping session
 * @param {Function} props.onClose - Function to call when the modal is closed
 * @param {Function} props.onSuccess - Function to call when scraping is successful
 */
function InteractiveScrapeModal({ projectId, url, sessionId, onClose, onSuccess }) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [forceRefresh, setForceRefresh] = useState(false);

  const handleScrape = async () => {
    setLoading(true);
    setError(null);

    try {
      // Execute scraping with the force refresh option
      const result = await executeScrape(projectId, url, sessionId, forceRefresh);

      // Call the success callback with the result
      if (onSuccess) {
        onSuccess(result);
      }

      // Close the modal
      if (onClose) {
        onClose();
      }
    } catch (err) {
      console.error('Error executing scrape:', err);
      setError(err.message || 'An error occurred while scraping the page');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="modal-overlay">
      <div className="modal-content">
        <div className="modal-header">
          <h2 className="modal-title">Interactive Scraping</h2>
          <button className="modal-close" onClick={onClose}>×</button>
        </div>

        <div className="modal-body">
          <div className="space-y-4">
            <div>
              <h3 className="text-lg font-medium">Ready to scrape this page?</h3>
              <p className="text-sm text-gray-500">
                Click the button below to scrape the current page and extract its content.
              </p>
            </div>

            <div className="p-3 bg-blue-50 border border-blue-200 rounded-md">
              <p className="text-sm font-medium">URL to scrape:</p>
              <p className="text-sm text-blue-800 break-all">{url}</p>
            </div>

            {/* Force Refresh Toggle */}
            <ForceRefreshToggle
              checked={forceRefresh}
              onChange={setForceRefresh}
              className="mt-4"
            />

            {error && (
              <div className="p-3 bg-red-50 border border-red-200 rounded-md">
                <p className="text-sm text-red-600">{error}</p>
              </div>
            )}
          </div>
        </div>

        <div className="modal-footer">
          <button
            className="btn btn-secondary"
            onClick={onClose}
            disabled={loading}
          >
            Cancel
          </button>
          <button
            className="btn btn-primary"
            onClick={handleScrape}
            disabled={loading}
          >
            {loading ? (
              <>
                <span className="animate-spin mr-2">⟳</span>
                Scraping...
              </>
            ) : (
              'Scrape This Page'
            )}
          </button>
        </div>
      </div>
    </div>
  );
}

export default InteractiveScrapeModal;
