import React, { useState } from 'react';
import { authService } from '../services/api';

const LoginButton = ({ onLoginSuccess }) => {
  const [loading, setLoading] = useState(false);

  const handleLogin = async () => {
    try {
      setLoading(true);
      const { auth_url } = await authService.getLoginUrl();
      window.location.href = auth_url;
    } catch (error) {
      console.error('Login error:', error);
      alert('Failed to initiate login');
      setLoading(false);
    }
  };

  return (
    <button
      onClick={handleLogin}
      disabled={loading}
      className="login-button"
    >
      {loading ? 'Connecting...' : '🔐 Sign in with Google'}
    </button>
  );
};

export default LoginButton;