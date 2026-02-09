import React, { useState, useRef, useEffect } from 'react';
import { chatService } from '../services/api';
import Message from './Message';

const ChatInterface = ({ userEmail }) => {
  const [messages, setMessages] = useState([
    { text: '👋 Hi! I\'m calPal. Try: "Add team meeting tomorrow at 2pm"', isUser: false }
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSend = async () => {
    if (!input.trim() || loading) return;

    const userMessage = input.trim();
    setInput('');
    
    // Add user message
    setMessages(prev => [...prev, { text: userMessage, isUser: true }]);
    setLoading(true);

    try {
      const response = await chatService.sendMessage(userMessage, userEmail);
      
      // Add bot response
      setMessages(prev => [
        ...prev,
        { text: response.message, isUser: false }
      ]);
    } catch (error) {
      console.error('Send error:', error);
      setMessages(prev => [
        ...prev,
        { text: '❌ Sorry, something went wrong. Please try again.', isUser: false }
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="chat-container">
      <div className="chat-header">
        <h2>calPal 📅</h2>
        <p className="user-email">{userEmail}</p>
      </div>

      <div className="messages-container">
        {messages.map((msg, idx) => (
          <Message key={idx} message={msg.text} isUser={msg.isUser} />
        ))}
        {loading && (
          <div className="typing-indicator">
            <span></span><span></span><span></span>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      <div className="input-container">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyPress={handleKeyPress}
          placeholder="Type your calendar command..."
          disabled={loading}
          className="message-input"
        />
        <button
          onClick={handleSend}
          disabled={loading || !input.trim()}
          className="send-button"
        >
          ➤
        </button>
      </div>
    </div>
  );
};

export default ChatInterface;