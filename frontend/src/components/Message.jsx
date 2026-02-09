import React from 'react';

const Message = ({ message, isUser }) => {
  return (
    <div className={`message ${isUser ? 'user-message' : 'bot-message'}`}>
      <div className="message-content">
        {message}
      </div>
    </div>
  );
};

export default Message;