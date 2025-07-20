import React from 'react';
import ReactMarkdown from 'react-markdown';

import { useChatRoom } from '../llm/hooks';

import './home-page.css';

function HomePage() {
  const [inputValue, setInputValue] = React.useState('');
  const { messages, sendMessage, sendMessageErrored, isPending } = useChatRoom();
  const messagesEndRef = React.useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  React.useEffect(() => {
    scrollToBottom();
  }, [messages]);

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
              <div className="message-text">
                <ReactMarkdown>{message.content}</ReactMarkdown>
              </div>
              <span className="message-time">{message.date}</span>
            </div>
          </div>
        ))}
        <div ref={messagesEndRef} />
      </div>

      <form className="chat-input-form" onSubmit={handleSendMessage}>
        <input
          type="text"
          value={inputValue}
          onChange={e => setInputValue(e.target.value)}
          placeholder="Type a message..."
          className="chat-input"
        />
        <button type="submit" className="send-button" disabled={!inputValue.trim() || isPending}>
          {isPending ? (
            <span className="loading-container">
              <span className="loading-spinner" />
              Sending...
            </span>
          ) : (
            'Send'
          )}
        </button>
      </form>
    </div>
  );
}

export default HomePage;
