/**
 * Component to guide users through Supabase setup
 */
import React from 'react';
import { AlertCircle, ExternalLink, Copy } from 'lucide-react';

function SupabaseSetupGuide() {
  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-900 via-blue-900 to-indigo-900 flex items-center justify-center p-4">
      <div className="max-w-4xl w-full bg-white/10 backdrop-blur-lg rounded-2xl border border-white/20 p-8">
        <div className="flex items-center gap-3 mb-6">
          <AlertCircle className="text-yellow-400" size={32} />
          <h1 className="text-3xl font-bold text-white">Supabase Configuration Required</h1>
        </div>
        
        <div className="text-purple-200 mb-8">
          <p className="text-lg mb-4">
            To use the authentication system, you need to set up Supabase. Follow these steps:
          </p>
        </div>

        <div className="space-y-6">
          <div className="bg-white/5 rounded-lg p-6 border border-white/10">
            <h2 className="text-xl font-semibold text-white mb-4 flex items-center gap-2">
              <span className="bg-purple-600 text-white rounded-full w-6 h-6 flex items-center justify-center text-sm">1</span>
              Create a Supabase Project
            </h2>
            <p className="text-purple-200 mb-3">
              Go to <a href="https://supabase.com" target="_blank" rel="noopener noreferrer" className="text-indigo-400 hover:text-indigo-300 inline-flex items-center gap-1">
                supabase.com <ExternalLink size={16} />
              </a> and create a new project.
            </p>
          </div>

          <div className="bg-white/5 rounded-lg p-6 border border-white/10">
            <h2 className="text-xl font-semibold text-white mb-4 flex items-center gap-2">
              <span className="bg-purple-600 text-white rounded-full w-6 h-6 flex items-center justify-center text-sm">2</span>
              Get Your Project Credentials
            </h2>
            <p className="text-purple-200 mb-3">
              In your Supabase dashboard, go to Settings → API to find:
            </p>
            <ul className="list-disc list-inside text-purple-200 space-y-1 ml-4">
              <li>Project URL</li>
              <li>Anon/Public Key</li>
            </ul>
          </div>

          <div className="bg-white/5 rounded-lg p-6 border border-white/10">
            <h2 className="text-xl font-semibold text-white mb-4 flex items-center gap-2">
              <span className="bg-purple-600 text-white rounded-full w-6 h-6 flex items-center justify-center text-sm">3</span>
              Update Your Environment Variables
            </h2>
            <p className="text-purple-200 mb-3">
              Update your <code className="bg-black/30 px-2 py-1 rounded">.env</code> file with your Supabase credentials:
            </p>
            <div className="bg-black/30 rounded-lg p-4 font-mono text-sm">
              <div className="flex items-center justify-between mb-2">
                <span className="text-gray-400"># .env file</span>
                <button 
                  onClick={() => copyToClipboard(`REACT_APP_SUPABASE_URL=https://your-project-id.supabase.co
REACT_APP_SUPABASE_ANON_KEY=your-supabase-anon-key`)}
                  className="text-indigo-400 hover:text-indigo-300 flex items-center gap-1"
                >
                  <Copy size={16} /> Copy
                </button>
              </div>
              <div className="text-green-400">
                REACT_APP_SUPABASE_URL=https://your-project-id.supabase.co<br />
                REACT_APP_SUPABASE_ANON_KEY=your-supabase-anon-key
              </div>
            </div>
          </div>

          <div className="bg-white/5 rounded-lg p-6 border border-white/10">
            <h2 className="text-xl font-semibold text-white mb-4 flex items-center gap-2">
              <span className="bg-purple-600 text-white rounded-full w-6 h-6 flex items-center justify-center text-sm">4</span>
              Run Database Migrations
            </h2>
            <p className="text-purple-200 mb-3">
              Execute the authentication migration script in your Supabase SQL editor:
            </p>
            <div className="bg-black/30 rounded-lg p-4 font-mono text-sm">
              <div className="flex items-center justify-between mb-2">
                <span className="text-gray-400"># Run in Supabase SQL Editor</span>
                <button 
                  onClick={() => copyToClipboard('backend/migrations/07_add_user_authentication.sql')}
                  className="text-indigo-400 hover:text-indigo-300 flex items-center gap-1"
                >
                  <Copy size={16} /> Copy Path
                </button>
              </div>
              <div className="text-yellow-400">
                backend/migrations/07_add_user_authentication.sql
              </div>
            </div>
          </div>

          <div className="bg-white/5 rounded-lg p-6 border border-white/10">
            <h2 className="text-xl font-semibold text-white mb-4 flex items-center gap-2">
              <span className="bg-purple-600 text-white rounded-full w-6 h-6 flex items-center justify-center text-sm">5</span>
              Restart the Application
            </h2>
            <p className="text-purple-200">
              After updating the environment variables, restart the development server to apply the changes.
            </p>
          </div>
        </div>

        <div className="mt-8 p-4 bg-blue-900/30 rounded-lg border border-blue-500/30">
          <p className="text-blue-200 text-sm">
            <strong>Note:</strong> The application will continue to work in demo mode until Supabase is configured. 
            Authentication features will show helpful error messages.
          </p>
        </div>
      </div>
    </div>
  );
}

export default SupabaseSetupGuide;
