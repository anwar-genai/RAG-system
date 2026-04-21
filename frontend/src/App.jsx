import { useState } from 'react';
import './App.css';
import ChatContainer from './components/ChatContainer';
import LoginForm from './components/LoginForm';
import authService from './services/auth';

function App() {
  const [loggedIn, setLoggedIn] = useState(authService.isLoggedIn());

  return loggedIn
    ? <ChatContainer onLogout={() => { authService.logout(); setLoggedIn(false); }} />
    : <LoginForm onLogin={() => setLoggedIn(true)} />;
}

export default App;
