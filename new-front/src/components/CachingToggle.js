import React from 'react';

/**
 * A toggle component for enabling/disabling caching
 *
 * @param {Object} props - Component props
 * @param {boolean} props.checked - Whether caching is enabled
 * @param {Function} props.onChange - Function to call when the toggle changes
 * @param {string} props.className - Additional CSS classes
 */
function CachingToggle({ checked, onChange, className = '' }) {
  return (
    <div className={`flex items-center space-x-2 ${className}`}>
      <div className="flex items-center">
        <input
          type="checkbox"
          id="caching-toggle"
          checked={checked}
          onChange={(e) => onChange(e.target.checked)}
          className="h-4 w-4 rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
        />
        <label htmlFor="caching-toggle" className="ml-2 block text-sm text-gray-700">
          Enable Caching
        </label>
      </div>
      <div className="text-xs text-gray-500">
        <span className={`inline-flex items-center rounded-full px-2 py-1 text-xs font-medium ${
          checked ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'
        }`}>
          {checked ? 'Caching Enabled' : 'Caching Disabled'}
        </span>
      </div>
      <div className="text-xs text-gray-500">
        <span className="tooltip" data-tooltip="When enabled, the system will use cached content when available. When disabled, fresh content will always be fetched.">
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

export default CachingToggle;
