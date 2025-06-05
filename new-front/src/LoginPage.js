import { useState } from 'react';
import { MessageCircle, Send, Globe, Plus,
         Trash2, Settings, AlertCircle, PlusCircle, XCircle,
         Download, RefreshCw, Lock, User, Key, Mail, Info,
         ChevronLeft, ChevronRight, ChevronDown, Eye, EyeOff } from 'lucide-react';
import { useAuth } from './contexts/AuthContext';
import { useToast } from './components/Toast';

function LoginPage() {
  const { signIn, signUp, loading, resendConfirmation } = useAuth();
  const toast = useToast();

  const [loginEmail, setLoginEmail] = useState('');
  const [loginPassword, setLoginPassword] = useState('');
  const [isSignUp, setIsSignUp] = useState(false);
  const [name, setName] = useState('');
  const [signupEmail, setSignupEmail] = useState('');
  const [signupPassword, setSignupPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [showEmailConfirmation, setShowEmailConfirmation] = useState(false);
  const [pendingEmail, setPendingEmail] = useState('');

  const handleLogin = async (e) => {
    e.preventDefault();

    if (!loginEmail || !loginPassword) {
      toast.error('Please fill in all fields');
      return;
    }

    try {
      const { data, error } = await signIn(loginEmail, loginPassword);

      if (error) {
        if (error.message.includes('Email not confirmed')) {
          setPendingEmail(loginEmail);
          setShowEmailConfirmation(true);
          toast.error('Please check your email and click the confirmation link before signing in.');
        } else {
          toast.error(error.message || 'Login failed');
        }
      } else {
        toast.success('Login successful!');
      }
    } catch (error) {
      toast.error('An unexpected error occurred');
    }
  };

  const handleSignup = async (e) => {
    e.preventDefault();

    if (!signupEmail || !signupPassword || !confirmPassword) {
      toast.error('Please fill in all fields');
      return;
    }

    if (signupPassword !== confirmPassword) {
      toast.error('Passwords do not match');
      return;
    }

    if (signupPassword.length < 6) {
      toast.error('Password must be at least 6 characters long');
      return;
    }

    try {
      const { data, error } = await signUp(signupEmail, signupPassword, name);

      if (error) {
        toast.error(error.message || 'Sign up failed');
      } else {
        setPendingEmail(signupEmail);
        setShowEmailConfirmation(true);
        toast.success('Account created successfully! Please check your email to verify your account.');
        // Clear form
        setName('');
        setSignupEmail('');
        setSignupPassword('');
        setConfirmPassword('');
      }
    } catch (error) {
      toast.error('An unexpected error occurred');
    }
  };

  const handleResendConfirmation = async () => {
    if (!pendingEmail) return;

    try {
      const { error } = await resendConfirmation(pendingEmail);

      if (error) {
        toast.error(error.message || 'Failed to resend confirmation email');
      } else {
        toast.success('Confirmation email sent! Please check your inbox.');
      }
    } catch (error) {
      toast.error('An unexpected error occurred');
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
        <div className="w-full max-w-md p-8 rounded-2xl glass-dark shadow-2xl border border-purple-500/30 animate-fadeIn">
          <div className="flex justify-center mb-6">
            <div className="p-3 rounded-full bg-gradient-to-r from-purple-600 to-indigo-600 shadow-lg">
              <Globe className="text-white" size={32} />
            </div>
          </div>

          <h2 className="text-3xl font-bold text-center text-white mb-2">
            {isSignUp ? "Create Account" : "Welcome Back"}
          </h2>
          <p className="text-center text-purple-300 mb-6">
            {showEmailConfirmation ? "Email Confirmation Required" :
             isSignUp ? "Join our web scraping platform" : "Sign in to your account"}
          </p>

          {showEmailConfirmation ? (
            // Email Confirmation Form
            <div className="text-center">
              <div className="mb-6">
                <div className="mx-auto w-16 h-16 bg-yellow-500/20 rounded-full flex items-center justify-center mb-4">
                  <Mail className="text-yellow-400" size={32} />
                </div>
                <p className="text-purple-200 mb-4">
                  We've sent a confirmation email to:
                </p>
                <p className="text-white font-semibold mb-4">{pendingEmail}</p>
                <p className="text-purple-300 text-sm mb-6">
                  Please check your inbox (and spam folder) and click the confirmation link to activate your account.
                </p>
              </div>

              <div className="space-y-4">
                <button
                  onClick={handleResendConfirmation}
                  disabled={loading}
                  className="w-full py-3 bg-yellow-600 hover:bg-yellow-500 rounded-lg font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {loading ? 'Sending...' : 'Resend Confirmation Email'}
                </button>

                <button
                  onClick={() => {
                    setShowEmailConfirmation(false);
                    setPendingEmail('');
                  }}
                  className="w-full py-3 bg-gray-600 hover:bg-gray-500 rounded-lg font-medium transition-colors"
                >
                  Back to Login
                </button>
              </div>
            </div>
          ) : !isSignUp ? (
            // Login Form
            <form onSubmit={handleLogin}>
              <div className="mb-4">
                <label className="block text-purple-200 text-sm font-medium mb-2">Email</label>
                <div className="relative">
                  <div className="absolute left-3 top-3 text-purple-400">
                    <Mail size={18} />
                  </div>
                  <input
                    type="email"
                    value={loginEmail}
                    onChange={(e) => setLoginEmail(e.target.value)}
                    className="input-primary pl-10"
                    placeholder="your@email.com"
                    required
                  />
                </div>
              </div>
              
              <div className="mb-6">
                <label className="block text-purple-200 text-sm font-medium mb-2">Password</label>
                <div className="relative">
                  <div className="absolute left-3 top-3 text-purple-400">
                    <Lock size={18} />
                  </div>
                  <input
                    type="password"
                    value={loginPassword}
                    onChange={(e) => setLoginPassword(e.target.value)}
                    className="input-primary pl-10"
                    placeholder="••••••••"
                    required
                  />
                </div>
                <div className="mt-2 text-right">
                  <a href="#" className="text-sm text-purple-300 hover:text-purple-200 transition-colors">Forgot password?</a>
                </div>
              </div>

              <button
                type="submit"
                disabled={loading}
                className="btn-primary w-full py-3 text-lg font-semibold disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {loading ? 'Signing In...' : 'Sign In'}
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
                disabled={loading}
                className="w-full py-3 bg-indigo-600 hover:bg-indigo-500 rounded-lg font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {loading ? 'Creating Account...' : 'Create Account'}
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