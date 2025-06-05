import { useState } from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import LoginPage from './LoginPage';
import WebScrapingDashboard from './Dashboard';
import { ToastProvider } from './components/Toast';

function App() {
  const [isLoggedIn, setIsLoggedIn] = useState(false);

  // Check for test mode in URL
  const isTestMode = window.location.search.includes('test=charts');

  const handleLogin = (credentials) => {
    if (credentials.email && credentials.password) {
      setIsLoggedIn(true);
    }
  };

  // Test mode disabled - removed test components

  return (
    <Router>
      <ToastProvider>
        <div className="App">
          <Routes>
            <Route path="/login" element={!isLoggedIn ? <LoginPage onLogin={handleLogin} /> : <WebScrapingDashboard />} />
            <Route path="/" element={!isLoggedIn ? <LoginPage onLogin={handleLogin} /> : <WebScrapingDashboard />} />
          </Routes>
        </div>
      </ToastProvider>
    </Router>
  );
}

export default App;