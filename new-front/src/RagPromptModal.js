import { Database, XCircle, AlertTriangle } from 'lucide-react';

function RagPromptModal({ isOpen, onClose, onDecision, projectName }) {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center z-50 p-4">
      <div className="bg-purple-800 p-6 rounded-lg shadow-xl w-full max-w-md border border-purple-600">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-xl font-semibold text-purple-100 flex items-center">
            <Database className="mr-2 text-teal-400" />
            Enable RAG for "{projectName}"?
          </h2>
          <button onClick={onClose} className="text-purple-300 hover:text-purple-100">
            <XCircle size={20} />
          </button>
        </div>
        <p className="text-purple-300 mb-3">
          Enabling RAG (Retrieval Augmented Generation) will allow the AI Chat to use the scraped content from this project (including all past and future scrapes) for more contextual and accurate answers.
        </p>
        <p className="text-purple-300 mb-6">
          This is a project-level setting.
        </p>
        
        <div className="space-y-3">
          <button
            onClick={() => onDecision('enabled')}
            className="w-full flex items-center justify-center space-x-2 px-4 py-3 bg-teal-600 hover:bg-teal-500 text-white rounded-md transition-colors focus:outline-none focus:ring-2 focus:ring-teal-400"
          >
            <span>Yes, Enable RAG</span>
          </button>
          <button
            onClick={() => onDecision('disabled')}
            className="w-full flex items-center justify-center space-x-2 px-4 py-3 bg-red-600 hover:bg-red-500 text-white rounded-md transition-colors focus:outline-none focus:ring-2 focus:ring-red-400"
          >
            <span>No, Disable RAG</span>
          </button>
          <button
            onClick={() => onDecision('prompt_later')}
            className="w-full flex items-center justify-center space-x-2 px-4 py-3 bg-purple-600 hover:bg-purple-500 text-white rounded-md transition-colors focus:outline-none focus:ring-2 focus:ring-purple-400"
          >
            <AlertTriangle size={16} className="mr-1" />
            <span>Decide Later</span>
          </button>
        </div>
        <p className="text-xs text-purple-400 mt-4 text-center">
          If you choose "Decide Later", you will be prompted again after the next scrape for this project.
        </p>
      </div>
    </div>
  );
}

export default RagPromptModal;