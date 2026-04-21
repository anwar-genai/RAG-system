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

  // If already logged in on mount but profile not cached (e.g. tokens survived a page refresh
  // before Phase A was deployed), fetch the profile now so role is available immediately.
  useEffect(() => {
    if (loggedIn && !authService.getUser()) {
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
