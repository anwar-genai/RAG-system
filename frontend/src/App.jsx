import { useState, useEffect } from 'react';
import './App.css';
import ChatContainer from './components/ChatContainer';
import LoginForm from './components/LoginForm';
import authService from './services/auth';

function App() {
  const [loggedIn, setLoggedIn] = useState(authService.isLoggedIn());

  // Sync auth state when another tab logs out via localStorage change
  useEffect(() => {
    const handleStorage = () => setLoggedIn(authService.isLoggedIn());
    window.addEventListener('storage', handleStorage);
    return () => window.removeEventListener('storage', handleStorage);
  }, []);

  return loggedIn
    ? <ChatContainer onLogout={() => { authService.logout(); setLoggedIn(false); }} />
    : <LoginForm onLogin={() => setLoggedIn(true)} />;
}

export default App;
