import { useState } from 'react';
import LoginPage from './LoginPage';
import WebScrapingDashboard from './Dashboard';

function App() {
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  
  const handleLogin = (credentials) => {
    if (credentials.email && credentials.password) {
      setIsLoggedIn(true);
    }
  };

  return (
    <div className="App">
      {!isLoggedIn ? (
        <LoginPage onLogin={handleLogin} />
      ) : (
        <WebScrapingDashboard />
      )}
    </div>
  );
}

export default App;