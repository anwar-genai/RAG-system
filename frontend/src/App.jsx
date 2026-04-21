import { useState, useEffect } from 'react';
import './App.css';
import ChatContainer from './components/ChatContainer';
import LoginForm from './components/LoginForm';
import AdminPanel from './components/AdminPanel';
import authService from './services/auth';

function App() {
  const [loggedIn, setLoggedIn] = useState(authService.isLoggedIn());
  const [view, setView] = useState('chat'); // 'chat' | 'admin'
  const [currentUser, setCurrentUser] = useState(authService.getUser());

  useEffect(() => {
    const handleStorage = () => {
      setLoggedIn(authService.isLoggedIn());
      setCurrentUser(authService.getUser());
    };
    window.addEventListener('storage', handleStorage);
    return () => window.removeEventListener('storage', handleStorage);
  }, []);

  const handleLogin = () => {
    setLoggedIn(true);
    setCurrentUser(authService.getUser());
  };

  const handleLogout = () => {
    authService.logout();
    setLoggedIn(false);
    setCurrentUser(null);
    setView('chat');
  };

  if (!loggedIn) return <LoginForm onLogin={handleLogin} />;

  if (view === 'admin') {
    return <AdminPanel currentUser={currentUser} onClose={() => setView('chat')} />;
  }

  return (
    <ChatContainer
      currentUser={currentUser}
      onLogout={handleLogout}
      onAdmin={currentUser?.role === 'admin' ? () => setView('admin') : null}
    />
  );
}

export default App;
