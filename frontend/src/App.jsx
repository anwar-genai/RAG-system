import { useState, useEffect } from 'react';
import './App.css';
import ChatContainer from './components/ChatContainer';
import LoginForm from './components/LoginForm';
import AdminPanel from './components/AdminPanel';
import MemorySettings from './components/MemorySettings';
import authService from './services/auth';

function App() {
  const [loggedIn, setLoggedIn] = useState(authService.isLoggedIn());
  const [view, setView] = useState('chat'); // 'chat' | 'admin' | 'memory'
  const [currentUser, setCurrentUser] = useState(authService.getUser());

  // Always re-fetch profile on mount so stale localStorage role data gets corrected.
  useEffect(() => {
    if (loggedIn) {
      authService._fetchAndCacheMe().then(user => {
        if (user) setCurrentUser(user);
      });
    }
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

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

  if (view === 'admin' && currentUser?.role === 'admin') {
    return <AdminPanel currentUser={currentUser} onClose={() => setView('chat')} />;
  }

  if (view === 'memory') {
    return <MemorySettings onClose={() => setView('chat')} />;
  }

  return (
    <ChatContainer
      currentUser={currentUser}
      onLogout={handleLogout}
      onAdmin={currentUser?.role === 'admin' ? () => setView('admin') : null}
      onMemorySettings={() => setView('memory')}
    />
  );
}

export default App;
