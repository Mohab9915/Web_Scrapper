import { useState } from 'react';
import LoginPage from './LoginPage';
import WebScrapingDashboard from './Dashboard';
import ChartIntegrationTest from './test/ChartIntegrationTest';
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

  // Show test component if in test mode
  if (isTestMode) {
    return (
      <ToastProvider>
        <ChartIntegrationTest />
      </ToastProvider>
    );
  }

  return (
    <ToastProvider>
      <div className="App">
        {!isLoggedIn ? (
          <LoginPage onLogin={handleLogin} />
        ) : (
          <WebScrapingDashboard />
        )}
      </div>
    </ToastProvider>
  );
}

export default App;