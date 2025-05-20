import React from 'react';
import './styles.css';

/**
 * A toggle component for the force refresh option
 *
 * @param {Object} props - Component props
 * @param {boolean} props.checked - Whether the toggle is checked
 * @param {Function} props.onChange - Function to call when the toggle changes
 * @param {string} props.className - Additional CSS classes
 */
function ForceRefreshToggle({ checked, onChange, className = '' }) {
  return (
    <div className={`flex items-center space-x-2 ${className}`}>
      <div className="flex items-center">
        <input
          type="checkbox"
          id="force-refresh-toggle"
          checked={checked}
          onChange={(e) => onChange(e.target.checked)}
          className="h-4 w-4 rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
        />
        <label htmlFor="force-refresh-toggle" className="ml-2 block text-sm text-gray-700">
          Force Refresh
        </label>
      </div>
      <div className="text-xs text-gray-500">
        <span className="inline-flex items-center rounded-full bg-blue-100 px-2 py-1 text-xs font-medium text-blue-700">
          Bypass Cache
        </span>
      </div>
      <div className="text-xs text-gray-500">
        <span className="tooltip" data-tooltip="When enabled, this option forces the system to fetch fresh content from the URL instead of using the cached version.">
          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-gray-400">
            <circle cx="12" cy="12" r="10"></circle>
            <path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"></path>
            <line x1="12" y1="17" x2="12.01" y2="17"></line>
          </svg>
        </span>
      </div>
    </div>
  );
}

export default ForceRefreshToggle;
