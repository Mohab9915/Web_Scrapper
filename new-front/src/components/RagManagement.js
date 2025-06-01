import React, { useState, useEffect } from 'react';
import { API_URL } from '../lib/api';

const RagManagement = ({ projectId, onStatusUpdate }) => {
  const [ragStatus, setRagStatus] = useState(null);
  const [loading, setLoading] = useState(false);
  const [ingestingSession, setIngestingSession] = useState(null);

  // Fetch RAG status
  const fetchRagStatus = async () => {
    try {
      const response = await fetch(`${API_URL}/projects/${projectId}/rag-status`);
      if (response.ok) {
        const status = await response.json();
        setRagStatus(status);
        if (onStatusUpdate) {
          onStatusUpdate(status);
        }
      }
    } catch (error) {
      console.error('Failed to fetch RAG status:', error);
    }
  };

  // Ingest session into RAG
  const ingestSession = async (sessionId) => {
    setIngestingSession(sessionId);
    setLoading(true);
    
    try {
      const response = await fetch(
        `${API_URL}/projects/${projectId}/sessions/${sessionId}/ingest-rag`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({}),
        }
      );

      if (response.ok) {
        const result = await response.json();
        console.log('RAG ingestion result:', result);
        
        // Show success message
        if (window.showToast) {
          window.showToast(
            `✅ RAG Ingestion Success! ${result.embeddings_created} embeddings created for ${result.data_items} items.`,
            'success'
          );
        }
        
        // Refresh status
        await fetchRagStatus();
      } else {
        const error = await response.text();
        console.error('RAG ingestion failed:', error);
        
        if (window.showToast) {
          window.showToast(`❌ RAG ingestion failed: ${error}`, 'error');
        }
      }
    } catch (error) {
      console.error('RAG ingestion error:', error);
      
      if (window.showToast) {
        window.showToast(`❌ RAG ingestion error: ${error.message}`, 'error');
      }
    } finally {
      setLoading(false);
      setIngestingSession(null);
    }
  };

  // Load status on mount
  useEffect(() => {
    if (projectId) {
      fetchRagStatus();
    }
  }, [projectId]);

  if (!ragStatus) {
    return (
      <div className="rag-management">
        <div className="loading">Loading RAG status...</div>
      </div>
    );
  }

  return (
    <div className="rag-management">
      <div className="rag-status-header">
        <h3>🤖 RAG System Status</h3>
        <button 
          onClick={fetchRagStatus}
          className="refresh-btn"
          disabled={loading}
        >
          🔄 Refresh
        </button>
      </div>

      <div className="rag-stats">
        <div className="stat-item">
          <span className="stat-label">RAG Enabled:</span>
          <span className={`stat-value ${ragStatus.rag_enabled ? 'enabled' : 'disabled'}`}>
            {ragStatus.rag_enabled ? '✅ Yes' : '❌ No'}
          </span>
        </div>
        
        <div className="stat-item">
          <span className="stat-label">Total Sessions:</span>
          <span className="stat-value stat-number">{ragStatus.total_sessions}</span>
        </div>

        <div className="stat-item">
          <span className="stat-label">RAG Ingested:</span>
          <span className="stat-value stat-number">{ragStatus.rag_ingested_sessions}</span>
        </div>

        <div className="stat-item">
          <span className="stat-label">Total Embeddings:</span>
          <span className="stat-value stat-number">{ragStatus.total_embeddings}</span>
        </div>
      </div>

      {ragStatus.sessions && ragStatus.sessions.length > 0 && (
        <div className="sessions-list">
          <h4>📋 Scraping Sessions</h4>
          <div className="sessions-container">
            {ragStatus.sessions.map((session) => (
              <div key={session.session_id} className="session-item">
                <div className="session-info">
                  <div className="session-url">
                    🌐 {session.url}
                  </div>
                  <div className="session-meta">
                    <span className="session-date">
                      📅 {new Date(session.scraped_at).toLocaleString()}
                    </span>
                    <span className={`session-status ${session.status}`}>
                      📊 {session.status}
                    </span>
                    <span className="session-embeddings">
                      🔗 {session.embeddings} embeddings
                    </span>
                  </div>
                </div>
                
                <div className="session-actions">
                  {session.has_structured_data && session.status !== 'rag_ingested' && (
                    <button
                      onClick={() => ingestSession(session.session_id)}
                      disabled={loading || ingestingSession === session.session_id}
                      className="ingest-btn"
                    >
                      {ingestingSession === session.session_id ? (
                        <>⏳ Ingesting...</>
                      ) : (
                        <>🚀 Ingest to RAG</>
                      )}
                    </button>
                  )}
                  
                  {session.status === 'rag_ingested' && (
                    <button
                      onClick={() => ingestSession(session.session_id)}
                      disabled={loading || ingestingSession === session.session_id}
                      className="reingest-btn"
                    >
                      {ingestingSession === session.session_id ? (
                        <>⏳ Re-ingesting...</>
                      ) : (
                        <>🔄 Re-ingest</>
                      )}
                    </button>
                  )}
                  
                  {!session.has_structured_data && (
                    <span className="no-data">❌ No structured data</span>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="rag-help">
        <h4>💡 RAG System Help</h4>
        <ul>
          <li><strong>RAG Enabled:</strong> Must be enabled for chat functionality</li>
          <li><strong>Ingested Sessions:</strong> Sessions processed for AI chat queries</li>
          <li><strong>Embeddings:</strong> Vector representations of your data for AI search</li>
          <li><strong>Re-ingest:</strong> Use when you want to update RAG data after re-scraping</li>
        </ul>
      </div>

      <style jsx>{`
        .rag-management {
          background: white;
          border-radius: 8px;
          padding: 20px;
          box-shadow: 0 2px 4px rgba(0,0,0,0.1);
          margin: 20px 0;
        }

        .rag-status-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 20px;
          border-bottom: 2px solid #f0f0f0;
          padding-bottom: 10px;
        }

        .rag-status-header h3 {
          margin: 0;
          color: #333;
        }

        .refresh-btn {
          background: #007bff;
          color: white;
          border: none;
          padding: 8px 16px;
          border-radius: 4px;
          cursor: pointer;
          font-size: 14px;
        }

        .refresh-btn:hover {
          background: #0056b3;
        }

        .refresh-btn:disabled {
          background: #ccc;
          cursor: not-allowed;
        }

        .rag-stats {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
          gap: 15px;
          margin-bottom: 20px;
        }

        .stat-item {
          display: flex;
          justify-content: space-between;
          padding: 10px;
          background: #f8f9fa;
          border-radius: 4px;
        }

        .stat-label {
          font-weight: 500;
          color: #666;
        }

        .stat-value {
          font-weight: bold;
        }

        .stat-value.enabled {
          color: #28a745;
        }

        .stat-value.disabled {
          color: #dc3545;
        }

        .stat-value.stat-number {
          color: #007bff;
          font-weight: bold;
        }

        .sessions-list h4 {
          margin: 20px 0 10px 0;
          color: #333;
        }

        .sessions-container {
          max-height: 400px;
          overflow-y: auto;
        }

        .session-item {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 15px;
          border: 1px solid #e0e0e0;
          border-radius: 6px;
          margin-bottom: 10px;
          background: #fafafa;
        }

        .session-info {
          flex: 1;
        }

        .session-url {
          font-weight: 500;
          color: #333;
          margin-bottom: 5px;
        }

        .session-meta {
          display: flex;
          gap: 15px;
          font-size: 12px;
          color: #666;
        }

        .session-status.rag_ingested {
          color: #28a745;
          font-weight: bold;
        }

        .session-status.scraped {
          color: #ffc107;
          font-weight: bold;
        }

        .session-actions {
          display: flex;
          gap: 10px;
        }

        .ingest-btn, .reingest-btn {
          background: #28a745;
          color: white;
          border: none;
          padding: 8px 16px;
          border-radius: 4px;
          cursor: pointer;
          font-size: 12px;
          white-space: nowrap;
        }

        .reingest-btn {
          background: #17a2b8;
        }

        .ingest-btn:hover {
          background: #218838;
        }

        .reingest-btn:hover {
          background: #138496;
        }

        .ingest-btn:disabled, .reingest-btn:disabled {
          background: #ccc;
          cursor: not-allowed;
        }

        .no-data {
          font-size: 12px;
          color: #dc3545;
          font-style: italic;
        }

        .rag-help {
          margin-top: 20px;
          padding: 15px;
          background: #e7f3ff;
          border-radius: 6px;
          border-left: 4px solid #007bff;
        }

        .rag-help h4 {
          margin: 0 0 10px 0;
          color: #333;
        }

        .rag-help ul {
          margin: 0;
          padding-left: 20px;
        }

        .rag-help li {
          margin-bottom: 5px;
          font-size: 14px;
          color: #555;
        }

        .loading {
          text-align: center;
          padding: 20px;
          color: #666;
        }
      `}</style>
    </div>
  );
};

export default RagManagement;
