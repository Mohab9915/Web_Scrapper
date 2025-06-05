import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import LoginPage from './LoginPage';
import WebScrapingDashboard from './Dashboard';
import { ToastProvider } from './components/Toast';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import SupabaseSetupGuide from './components/SupabaseSetupGuide';

// Protected Route component
function ProtectedRoute({ children }) {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-purple-900 via-blue-900 to-indigo-900 flex items-center justify-center">
        <div className="text-white text-xl">Loading...</div>
      </div>
    );
  }

  return user ? children : <Navigate to="/login" replace />;
}

// Public Route component (redirects to dashboard if already logged in)
function PublicRoute({ children }) {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-purple-900 via-blue-900 to-indigo-900 flex items-center justify-center">
        <div className="text-white text-xl">Loading...</div>
      </div>
    );
  }

  return user ? <Navigate to="/" replace /> : children;
}

function AppRoutes() {
  return (
    <Routes>
      <Route
        path="/login"
        element={
          <PublicRoute>
            <LoginPage />
          </PublicRoute>
        }
      />
      <Route
        path="/"
        element={
          <ProtectedRoute>
            <WebScrapingDashboard />
          </ProtectedRoute>
        }
      />
    </Routes>
  );
}

function App() {
  // Check if Supabase is configured
  const supabaseUrl = process.env.REACT_APP_SUPABASE_URL;
  const supabaseAnonKey = process.env.REACT_APP_SUPABASE_ANON_KEY;

  // Debug logging
  console.log('🔍 App.js Debug:');
  console.log('  - supabaseUrl:', supabaseUrl);
  console.log('  - supabaseAnonKey:', supabaseAnonKey ? '[HIDDEN]' : 'Not set');

  const isSupabaseConfigured = supabaseUrl &&
    supabaseAnonKey &&
    supabaseUrl !== 'https://your-project-id.supabase.co' &&
    supabaseUrl !== 'https://your-actual-project-id.supabase.co' &&
    supabaseAnonKey !== 'your-supabase-anon-key' &&
    supabaseAnonKey !== 'your-actual-anon-key-here';

  console.log('  - isSupabaseConfigured:', isSupabaseConfigured);

  // Show setup guide if Supabase is not configured
  if (!isSupabaseConfigured) {
    return (
      <ToastProvider>
        <SupabaseSetupGuide />
      </ToastProvider>
    );
  }

  return (
    <AuthProvider>
      <Router>
        <ToastProvider>
          <div className="App">
            <AppRoutes />
          </div>
        </ToastProvider>
      </Router>
    </AuthProvider>
  );
}

export default App;