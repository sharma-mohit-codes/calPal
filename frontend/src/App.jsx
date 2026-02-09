import React, { useState, useEffect } from 'react';
import ChatInterface from './components/ChatInterface';
import LoginButton from './components/LoginButton';
import './App.css';

function App() {
  const [user, setUser] = useState(null);

  useEffect(() => {
    // Check for login success from OAuth callback
    const params = new URLSearchParams(window.location.search);
    const loginStatus = params.get('login');
    const email = params.get('email');

    if (loginStatus === 'success' && email) {
      setUser({ email });
      localStorage.setItem('userEmail', email);
      // Clean URL
      window.history.replaceState({}, document.title, '/');
    } else {
      // Check localStorage for existing session
      const savedEmail = localStorage.getItem('userEmail');
      if (savedEmail) {
        setUser({ email: savedEmail });
      }
    }
  }, []);

  const handleLogout = () => {
    localStorage.removeItem('userEmail');
    setUser(null);
  };

  return (
    <div className="app">
      {!user ? (
        <div className="login-screen">
          <div className="login-card">
            <h1>📅 calPal</h1>
            <p>Your AI-powered calendar assistant</p>
            <LoginButton onLoginSuccess={setUser} />
          </div>
        </div>
      ) : (
        <>
          <ChatInterface userEmail={user.email} />
          <button onClick={handleLogout} className="logout-button">
            Logout
          </button>
        </>
      )}
    </div>
  );
}

export default App;