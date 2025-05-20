import { useState, useEffect } from 'react';
import { X, Key, Info, Eye, EyeOff, Save, FileJson, FileCsv, Database } from 'lucide-react';
import CachingToggle from './components/CachingToggle';

function ApiKeyInstructionsModal({ provider, onClose }) {
  let content = <p>Instructions for obtaining an API key for {provider} would appear here.</p>;

  if (provider === 'OpenAI') {
    content = (
      <>
        <p className="mb-2">To get your OpenAI API Key:</p>
        <ol className="list-decimal list-inside text-sm space-y-1">
          <li>Go to <a href="https://platform.openai.com/api-keys" target="_blank" rel="noopener noreferrer" className="text-indigo-400 hover:underline">platform.openai.com/api-keys</a>.</li>
          <li>Log in or sign up for an OpenAI account.</li>
          <li>Click on "Create new secret key".</li>
          <li>Copy the generated key and paste it into the input field.</li>
          <li><strong>Important:</strong> Keep your API key confidential.</li>
        </ol>
      </>
    );
  } else if (provider === 'Google AI (Gemini)') {
    content = (
      <>
        <p className="mb-2">To get your Google AI (Gemini) API Key:</p>
        <ol className="list-decimal list-inside text-sm space-y-1">
          <li>Go to <a href="https://aistudio.google.com/app/apikey" target="_blank" rel="noopener noreferrer" className="text-indigo-400 hover:underline">Google AI Studio</a>.</li>
          <li>Sign in with your Google account.</li>
          <li>Click on "Get API key" or "Create API key in new project".</li>
          <li>Copy the generated API key.</li>
          <li><strong>Important:</strong> Enable the Generative Language API in your Google Cloud project if necessary.</li>
        </ol>
      </>
    );
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-80 flex items-center justify-center z-[60] p-4">
      <div className="bg-purple-700 p-6 rounded-lg shadow-xl w-full max-w-lg border border-purple-600">
        <div className="flex justify-between items-center mb-3">
          <h3 className="text-lg font-semibold text-purple-100">How to get {provider} API Key</h3>
          <button onClick={onClose} className="text-purple-300 hover:text-purple-100"><X size={20} /></button>
        </div>
        <div className="text-purple-200 text-sm leading-relaxed">{content}</div>
        <button
          onClick={onClose}
          className="mt-4 px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white text-sm rounded-md w-full"
        >
          Close Instructions
        </button>
      </div>
    </div>
  );
}


function SettingsModal({ isOpen, onClose }) {
  const [openaiApiKey, setOpenaiApiKey] = useState('');
  const [geminiApiKey, setGeminiApiKey] = useState('');
  const [showOpenaiKey, setShowOpenaiKey] = useState(false);
  const [showGeminiKey, setShowGeminiKey] = useState(false);
  const [defaultExportFormat, setDefaultExportFormat] = useState('json');
  const [cachingEnabled, setCachingEnabled] = useState(true);
  const [instructionProvider, setInstructionProvider] = useState(null);

  useEffect(() => {
    if (isOpen) {
      setOpenaiApiKey(localStorage.getItem('openaiApiKey') || '');
      setGeminiApiKey(localStorage.getItem('geminiApiKey') || '');
      setDefaultExportFormat(localStorage.getItem('defaultExportFormat') || 'json');
      setCachingEnabled(localStorage.getItem('cachingEnabled') !== 'false'); // Default to true if not set
    }
  }, [isOpen]);

  const handleSaveSettings = () => {
    localStorage.setItem('openaiApiKey', openaiApiKey);
    localStorage.setItem('geminiApiKey', geminiApiKey);
    localStorage.setItem('defaultExportFormat', defaultExportFormat);
    localStorage.setItem('cachingEnabled', cachingEnabled.toString());
    alert('Settings saved!');
    onClose();
  };

  if (!isOpen) {
    return null;
  }

  return (
    <>
      <div className="fixed inset-0 bg-black bg-opacity-70 flex items-center justify-center z-50 p-4 overflow-y-auto">
        <div className="bg-purple-800 p-6 rounded-lg shadow-xl w-full max-w-lg border border-purple-700 relative my-8">
          <button
            onClick={onClose}
            className="absolute top-4 right-4 text-purple-300 hover:text-purple-100"
            aria-label="Close settings"
          >
            <X size={24} />
          </button>
          <h2 className="text-2xl font-semibold text-purple-100 mb-6">Application Settings</h2>

          <div className="space-y-6">
            <section>
              <h3 className="text-lg font-medium text-purple-200 mb-3 border-b border-purple-700 pb-2 flex items-center">
                <Key size={20} className="mr-2 text-purple-300" /> API Keys
              </h3>
              <div className="space-y-4">
                <div>
                  <label htmlFor="openai-api-key" className="block text-sm font-medium text-purple-300 mb-1">
                    OpenAI API Key
                  </label>
                  <div className="flex items-center space-x-2">
                    <input
                      id="openai-api-key"
                      type={showOpenaiKey ? 'text' : 'password'}
                      value={openaiApiKey}
                      onChange={(e) => setOpenaiApiKey(e.target.value)}
                      placeholder="sk-..."
                      className="flex-grow p-2 rounded-md bg-purple-700 border border-purple-600 text-white placeholder-purple-400 focus:outline-none focus:ring-2 focus:ring-purple-400"
                    />
                    <button
                      type="button"
                      onClick={() => setShowOpenaiKey(!showOpenaiKey)}
                      className="p-2 text-purple-300 hover:text-purple-100"
                      title={showOpenaiKey ? "Hide Key" : "Show Key"}
                    >
                      {showOpenaiKey ? <EyeOff size={18} /> : <Eye size={18} />}
                    </button>
                  </div>
                  <button
                    onClick={() => setInstructionProvider('OpenAI')}
                    className="mt-1 text-xs text-indigo-400 hover:underline flex items-center"
                  >
                    <Info size={12} className="mr-1" /> How to get this key?
                  </button>
                </div>

                <div>
                  <label htmlFor="gemini-api-key" className="block text-sm font-medium text-purple-300 mb-1">
                    Google AI (Gemini) API Key
                  </label>
                   <div className="flex items-center space-x-2">
                    <input
                      id="gemini-api-key"
                      type={showGeminiKey ? 'text' : 'password'}
                      value={geminiApiKey}
                      onChange={(e) => setGeminiApiKey(e.target.value)}
                      placeholder="AIza..."
                      className="flex-grow p-2 rounded-md bg-purple-700 border border-purple-600 text-white placeholder-purple-400 focus:outline-none focus:ring-2 focus:ring-purple-400"
                    />
                     <button
                      type="button"
                      onClick={() => setShowGeminiKey(!showGeminiKey)}
                      className="p-2 text-purple-300 hover:text-purple-100"
                      title={showGeminiKey ? "Hide Key" : "Show Key"}
                    >
                      {showGeminiKey ? <EyeOff size={18} /> : <Eye size={18} />}
                    </button>
                  </div>
                  <button
                    onClick={() => setInstructionProvider('Google AI (Gemini)')}
                    className="mt-1 text-xs text-indigo-400 hover:underline flex items-center"
                  >
                    <Info size={12} className="mr-1" /> How to get this key?
                  </button>
                </div>
                <p className="text-xs text-purple-400">
                  API keys are stored locally in your browser's localStorage.
                </p>
              </div>
            </section>

            <section>
              <h3 className="text-lg font-medium text-purple-200 mb-3 border-b border-purple-700 pb-2">Data Preferences</h3>
              <div className="space-y-3">
                <div>
                  <label htmlFor="default-export-format" className="block text-sm font-medium text-purple-300 mb-1">
                    Default Export Format
                  </label>
                  <select
                    id="default-export-format"
                    value={defaultExportFormat}
                    onChange={(e) => setDefaultExportFormat(e.target.value)}
                    className="w-full p-2 rounded-md bg-purple-700 border border-purple-600 text-white focus:outline-none focus:ring-2 focus:ring-purple-400"
                  >
                    <option value="json">JSON (.json)</option>
                    <option value="csv">CSV (.csv)</option>
                  </select>
                  <p className="text-xs text-purple-400 mt-1">
                    Choose the default file format for downloading scraped data.
                  </p>
                </div>
              </div>
            </section>

            <section>
              <h3 className="text-lg font-medium text-purple-200 mb-3 border-b border-purple-700 pb-2 flex items-center">
                <Database size={20} className="mr-2 text-purple-300" /> Caching Settings
              </h3>
              <div className="space-y-3">
                <div className="bg-purple-700 p-3 rounded-md">
                  <CachingToggle
                    checked={cachingEnabled}
                    onChange={setCachingEnabled}
                    className="text-purple-200"
                  />
                  <p className="text-xs text-purple-400 mt-2">
                    When caching is enabled, the system will use cached content when available to improve performance and reduce API usage.
                    When disabled, fresh content will always be fetched from the source.
                  </p>
                </div>
              </div>
            </section>
          </div>

          <div className="mt-8 flex justify-end space-x-3">
            <button
              onClick={onClose}
              className="px-4 py-2 bg-purple-600 hover:bg-purple-500 text-white rounded-md text-sm"
            >
              Cancel
            </button>
            <button
              onClick={handleSaveSettings}
              className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-md text-sm flex items-center"
            >
              <Save size={16} className="mr-2"/>
              Save Settings
            </button>
          </div>
        </div>
      </div>

      {instructionProvider && (
        <ApiKeyInstructionsModal
          provider={instructionProvider}
          onClose={() => setInstructionProvider(null)}
        />
      )}
    </>
  );
}

export default SettingsModal;