import React, { useState, useEffect } from 'react';
import ChatInterface from './components/ChatInterface';
import LoginButton from './components/LoginButton';
import './App.css';

function App() {
  const [user, setUser] = useState(null);
  const [theme, setTheme] = useState('dark');

  useEffect(() => {
    // Load saved theme
    const savedTheme = localStorage.getItem('theme') || 'dark';
    setTheme(savedTheme);
    document.documentElement.setAttribute('data-theme', savedTheme);

    // Check for login success from OAuth callback
    const params = new URLSearchParams(window.location.search);
    const loginStatus = params.get('login');
    const email = params.get('email');

    if (loginStatus === 'success' && email) {
      setUser({ email });
      localStorage.setItem('userEmail', email);
      window.history.replaceState({}, document.title, '/');
    } else {
      const savedEmail = localStorage.getItem('userEmail');
      if (savedEmail) {
        setUser({ email: savedEmail });
      }
    }
  }, []);

  const toggleTheme = () => {
    const newTheme = theme === 'dark' ? 'light' : 'dark';
    setTheme(newTheme);
    localStorage.setItem('theme', newTheme);
    document.documentElement.setAttribute('data-theme', newTheme);
  };

  const handleLogout = () => {
    localStorage.removeItem('userEmail');
    setUser(null);
  };

  return (
    <div className="app">
      {!user ? (
        <div className="login-screen">
          <div className="theme-toggle-login">
            <button onClick={toggleTheme} className="theme-btn" title="Toggle theme">
              {theme === 'dark' ? '☀️' : '🌙'}
            </button>
          </div>
          
          <div className="login-container">
            <div className="login-left">
              <div className="logo-section">
                <div className="logo-icon">📅</div>
                <h1 className="brand-name">calPal</h1>
                <p className="tagline">Your intelligent calendar assistant</p>
              </div>
              
              <div className="features">
                <div className="feature">
                  <span className="feature-icon">🤖</span>
                  <div>
                    <h3>AI-Powered</h3>
                    <p>Natural language understanding</p>
                  </div>
                </div>
                <div className="feature">
                  <span className="feature-icon">⚡</span>
                  <div>
                    <h3>Lightning Fast</h3>
                    <p>Instant calendar management</p>
                  </div>
                </div>
                <div className="feature">
                  <span className="feature-icon">🔒</span>
                  <div>
                    <h3>Secure</h3>
                    <p>Google OAuth protection</p>
                  </div>
                </div>
              </div>
            </div>

            <div className="login-right">
              <div className="login-card">
                <h2>Welcome Back</h2>
                <p className="login-subtitle">Sign in to manage your calendar with AI</p>
                
                <LoginButton onLoginSuccess={setUser} />
              </div>
            </div>
          </div>
        </div>
      ) : (
        <>
          <ChatInterface userEmail={user.email} theme={theme} />
          <div className="top-bar">
            <button onClick={toggleTheme} className="theme-toggle" title="Toggle theme">
              {theme === 'dark' ? '☀️' : '🌙'}
            </button>
            <button onClick={handleLogout} className="logout-btn">
              Logout
            </button>
          </div>
        </>
      )}
    </div>
  );
}

export default App;