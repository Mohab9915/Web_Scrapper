import { useState } from 'react';
import { MessageCircle, Send, Globe, Plus,
         Trash2, Settings, AlertCircle, PlusCircle, XCircle, 
         Download, RefreshCw, Lock, User, Key, Mail, Info, 
         ChevronLeft, ChevronRight, ChevronDown } from 'lucide-react';

function LoginPage({ onLogin }) {

  const [loginEmail, setLoginEmail] = useState('');
  const [loginPassword, setLoginPassword] = useState('');
  const [isSignUp, setIsSignUp] = useState(false);
  const [name, setName] = useState('');
  const [signupEmail, setSignupEmail] = useState('');
  const [signupPassword, setSignupPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');

  const handleLogin = (e) => {
    e.preventDefault();
    if (loginEmail && loginPassword) {
      onLogin({ email: loginEmail, password: loginPassword });
    }
  };

  const handleSignup = (e) => {
    e.preventDefault();
    if (signupEmail && signupPassword && confirmPassword === signupPassword) {
      alert('Account created! Please log in.');
      setIsSignUp(false);
    }
  };

  return (
    <div className="flex h-screen bg-purple-900 text-white">
      {/* Stars background */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        {[...Array(100)].map((_, i) => (
          <div 
            key={i}
            className="absolute rounded-full bg-white"
            style={{
              width: Math.random() * 3 + 'px',
              height: Math.random() * 3 + 'px',
              top: Math.random() * 100 + '%',
              left: Math.random() * 100 + '%',
              opacity: Math.random() * 0.8
            }}
          ></div>
        ))}
      </div>
      
      {/* Left side - login form */}
      <div className="flex-1 flex items-center justify-center relative z-10">
        <div className="w-full max-w-md p-8 rounded-lg bg-purple-800 bg-opacity-70 shadow-xl border border-purple-600">
          <div className="flex justify-center mb-6">
            <Globe className="text-purple-300" size={40} />
          </div>
          
          <h2 className="text-3xl font-bold text-center text-purple-200 mb-6">
            {isSignUp ? "Create Account" : "Welcome Back"}
          </h2>
          
          {!isSignUp ? (
            // Login Form
            <form onSubmit={handleLogin}>
              <div className="mb-4">
                <label className="block text-purple-300 text-sm mb-2">Email</label>
                <div className="relative">
                  <div className="absolute left-3 top-3 text-purple-400">
                    <Mail size={18} />
                  </div>
                  <input 
                    type="email" 
                    value={loginEmail}
                    onChange={(e) => setLoginEmail(e.target.value)}
                    className="w-full p-3 pl-10 rounded-lg bg-purple-700 border border-purple-600 text-white placeholder-purple-400 focus:outline-none focus:ring-2 focus:ring-purple-400"
                    placeholder="your@email.com"
                    required
                  />
                </div>
              </div>
              
              <div className="mb-6">
                <label className="block text-purple-300 text-sm mb-2">Password</label>
                <div className="relative">
                  <div className="absolute left-3 top-3 text-purple-400">
                    <Lock size={18} />
                  </div>
                  <input 
                    type="password" 
                    value={loginPassword}
                    onChange={(e) => setLoginPassword(e.target.value)}
                    className="w-full p-3 pl-10 rounded-lg bg-purple-700 border border-purple-600 text-white placeholder-purple-400 focus:outline-none focus:ring-2 focus:ring-purple-400"
                    placeholder="••••••••"
                    required
                  />
                </div>
                <div className="mt-2 text-right">
                  <a href="#" className="text-sm text-purple-300 hover:text-purple-200">Forgot password?</a>
                </div>
              </div>
              
              <button 
                type="submit" 
                className="w-full py-3 bg-indigo-600 hover:bg-indigo-500 rounded-lg font-medium transition-colors"
              >
                Log In
              </button>
              
              <div className="mt-6 text-center">
                <p className="text-purple-300">
                  Don't have an account?{" "}
                  <button 
                    type="button"
                    onClick={() => setIsSignUp(true)}
                    className="text-indigo-400 hover:text-indigo-300 font-medium"
                  >
                    Sign Up
                  </button>
                </p>
              </div>
            </form>
          ) : (
            // Signup Form
            <form onSubmit={handleSignup}>
              <div className="mb-4">
                <label className="block text-purple-300 text-sm mb-2">Name</label>
                <div className="relative">
                  <div className="absolute left-3 top-3 text-purple-400">
                    <User size={18} />
                  </div>
                  <input 
                    type="text" 
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    className="w-full p-3 pl-10 rounded-lg bg-purple-700 border border-purple-600 text-white placeholder-purple-400 focus:outline-none focus:ring-2 focus:ring-purple-400"
                    placeholder="Your name"
                    required
                  />
                </div>
              </div>
              
              <div className="mb-4">
                <label className="block text-purple-300 text-sm mb-2">Email</label>
                <div className="relative">
                  <div className="absolute left-3 top-3 text-purple-400">
                    <Mail size={18} />
                  </div>
                  <input 
                    type="email" 
                    value={signupEmail}
                    onChange={(e) => setSignupEmail(e.target.value)}
                    className="w-full p-3 pl-10 rounded-lg bg-purple-700 border border-purple-600 text-white placeholder-purple-400 focus:outline-none focus:ring-2 focus:ring-purple-400"
                    placeholder="your@email.com"
                    required
                  />
                </div>
              </div>
              
              <div className="mb-4">
                <label className="block text-purple-300 text-sm mb-2">Password</label>
                <div className="relative">
                  <div className="absolute left-3 top-3 text-purple-400">
                    <Key size={18} />
                  </div>
                  <input 
                    type="password" 
                    value={signupPassword}
                    onChange={(e) => setSignupPassword(e.target.value)}
                    className="w-full p-3 pl-10 rounded-lg bg-purple-700 border border-purple-600 text-white placeholder-purple-400 focus:outline-none focus:ring-2 focus:ring-purple-400"
                    placeholder="••••••••"
                    required
                  />
                </div>
              </div>
              
              <div className="mb-6">
                <label className="block text-purple-300 text-sm mb-2">Confirm Password</label>
                <div className="relative">
                  <div className="absolute left-3 top-3 text-purple-400">
                    <Lock size={18} />
                  </div>
                  <input 
                    type="password" 
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                    className="w-full p-3 pl-10 rounded-lg bg-purple-700 border border-purple-600 text-white placeholder-purple-400 focus:outline-none focus:ring-2 focus:ring-purple-400"
                    placeholder="••••••••"
                    required
                  />
                </div>
              </div>
              
              <button 
                type="submit" 
                className="w-full py-3 bg-indigo-600 hover:bg-indigo-500 rounded-lg font-medium transition-colors"
              >
                Create Account
              </button>
              
              <div className="mt-6 text-center">
                <p className="text-purple-300">
                  Already have an account?{" "}
                  <button 
                    type="button"
                    onClick={() => setIsSignUp(false)}
                    className="text-indigo-400 hover:text-indigo-300 font-medium"
                  >
                    Log In
                  </button>
                </p>
              </div>
            </form>
          )}
        </div>
      </div>
      
      {/* Right side - feature showcase */}
      <div className="hidden lg:flex lg:flex-1 flex-col justify-center p-12 relative z-10">
        <div className="max-w-lg">
          <h1 className="text-5xl font-bold mb-6 text-purple-200">
            Web Scraping Tool <span className="text-indigo-400"></span>
          </h1>
          
          <p className="text-xl text-purple-300 mb-10">
            Transform the way you collect data from the web. Our scraping tool helps you extract, analyze, and utilize web data effortlessly.
          </p>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="bg-purple-800 bg-opacity-50 p-6 rounded-lg border border-purple-700">
              <div className="text-indigo-400 mb-3">
                <Globe size={28} />
              </div>
              <h3 className="text-xl font-semibold mb-2 text-purple-200">Multiple URL Scraping</h3>
              <p className="text-purple-300">
                Extract data from multiple websites simultaneously .
              </p>
            </div>
            
            <div className="bg-purple-800 bg-opacity-50 p-6 rounded-lg border border-purple-700">
              <div className="text-indigo-400 mb-3">
                <MessageCircle size={28} />
              </div>
              <h3 className="text-xl font-semibold mb-2 text-purple-200">AI-Powered Chat</h3>
              <p className="text-purple-300">
                Communicate with our AI to describe what data you need and how you want it extracted.
              </p>
            </div>
            
            <div className="bg-purple-800 bg-opacity-50 p-6 rounded-lg border border-purple-700">
              <div className="text-indigo-400 mb-3">
                <Download size={28} />
              </div>
              <h3 className="text-xl font-semibold mb-2 text-purple-200">Easy Export</h3>
              <p className="text-purple-300">
                Download your scraped data in multiple formats including CSV, JSON, and Excel.
              </p>
            </div>
            
            <div className="bg-purple-800 bg-opacity-50 p-6 rounded-lg border border-purple-700">
              <div className="text-indigo-400 mb-3">
                <Settings size={28} />
              </div>
              <h3 className="text-xl font-semibold mb-2 text-purple-200">Custom Configurations</h3>
              <p className="text-purple-300">
                Set up custom scraping rules, schedules, and notifications for your data collection needs.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
export default LoginPage; 