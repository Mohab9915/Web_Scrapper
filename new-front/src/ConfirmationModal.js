import { XCircle, AlertTriangle } from 'lucide-react';

function ConfirmationModal({ 
  isOpen, 
  onClose, 
  onConfirm, 
  title, 
  message, 
  confirmButtonText = "Delete", 
  isDeleting = false,
  itemName = "",
  itemType = "item"
}) {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center z-50 p-4">
      <div className="bg-purple-800 p-6 rounded-lg shadow-xl w-full max-w-md border border-purple-600">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-xl font-semibold text-purple-100 flex items-center">
            <AlertTriangle className="mr-2 text-red-400" size={20} />
            {title || `Delete ${itemType}?`}
          </h2>
          <button onClick={onClose} className="text-purple-300 hover:text-purple-100">
            <XCircle size={20} />
          </button>
        </div>
        
        <p className="text-purple-300 mb-6">
          {message || `Are you sure you want to delete ${itemName ? `"${itemName}"` : `this ${itemType}`}? This action cannot be undone.`}
        </p>
        
        <div className="flex justify-end space-x-3">
          <button
            onClick={onClose}
            disabled={isDeleting}
            className="px-4 py-2 bg-purple-700 hover:bg-purple-600 text-white rounded-md transition-colors focus:outline-none focus:ring-2 focus:ring-purple-400 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Cancel
          </button>
          <button
            onClick={onConfirm}
            disabled={isDeleting}
            className="px-4 py-2 bg-red-600 hover:bg-red-500 text-white rounded-md transition-colors focus:outline-none focus:ring-2 focus:ring-red-400 disabled:opacity-50 disabled:cursor-not-allowed flex items-center"
          >
            {isDeleting ? (
              <>
                <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                Deleting...
              </>
            ) : (
              confirmButtonText
            )}
          </button>
        </div>
      </div>
    </div>
  );
}

export default ConfirmationModal;
