import React from 'react';

import { useChatRoom } from '../llm/hooks';

import './home-page.css';

function HomePage() {
  const [inputValue, setInputValue] = React.useState('');
  const { messages, sendMessage, sendMessageErrored } = useChatRoom();

  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    const message = inputValue.trim();
    if (!message) return;

    await sendMessage({ message });
    if (sendMessageErrored) return;

    setInputValue('');
  };

  return (
    <div className="chat-app">
      <div className="chat-header">
        <h1>Agents Play</h1>
      </div>

      <div className="chat-messages">
        {messages.map(message => (
          <div key={message.id} className={`message ${message.role === 'user' ? 'user-message' : 'other-message'}`}>
            <div className="message-content">
              <span className="message-text">{message.content}</span>
              <span className="message-time">{message.date}</span>
            </div>
          </div>
        ))}
      </div>

      <form className="chat-input-form" onSubmit={handleSendMessage}>
        <input
          type="text"
          value={inputValue}
          onChange={e => setInputValue(e.target.value)}
          placeholder="Type a message..."
          className="chat-input"
        />
        <button type="submit" className="send-button" disabled={!inputValue.trim()}>
          Send
        </button>
      </form>
    </div>
  );
}

export default HomePage;
