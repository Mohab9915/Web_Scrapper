import { useState } from 'react';
import LoginPage from './LoginPage';
import WebScrapingDashboard from './Dashboard';
import { ToastProvider } from './components/Toast';

function App() {
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  
  const handleLogin = (credentials) => {
    if (credentials.email && credentials.password) {
      setIsLoggedIn(true);
    }
  };

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