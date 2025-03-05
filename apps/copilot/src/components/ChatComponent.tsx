import { Form } from 'react-bootstrap';
import { useState, KeyboardEvent, useEffect, useRef } from 'react';
import { ChatMessage, bedrockService } from '../services/BedrockService';

const ChatComponent = () => {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const chatContainerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (chatContainerRef.current) {
      chatContainerRef.current.scrollTop = chatContainerRef.current.scrollHeight;
    }
  }, [messages, isLoading]);

  const handleSendMessage = async () => {
    if (!inputValue.trim() || isLoading) return;

    const userMessage: ChatMessage = {
      role: 'user',
      content: inputValue
    };

    setIsLoading(true);
    setInputValue('');
    setMessages(prev => [...prev, userMessage]);

    try {
      const newMessages = [...messages, userMessage];
      const response = await bedrockService.sendChatMessage(newMessages);
      
      const assistantMessage: ChatMessage = {
        role: 'assistant',
        content: response
      };

      setMessages(prev => [...prev, assistantMessage]);
    } catch (error) {
      console.error('Error in chat:', error);
      // Optionally show error message to user
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  return (
    <div className="search-column">
      <h4>Document Chat</h4>
      <div className="chat-results" ref={chatContainerRef}>
        {messages.length > 0 ? (
          messages.map((message, index) => (
            <div
              key={index}
              className={`message ${message.role} mb-2 p-2 ${
                message.role === 'assistant' ? 'bg-light' : 'bg-primary text-white'
              } rounded`}
            >
              <div className="message-content">{message.content}</div>
            </div>
          ))
        ) : (
          <p className="text-muted">Start a conversation by typing a message</p>
        )}
        {isLoading && (
          <div className="message assistant mb-2 p-2 bg-light rounded">
            <div className="message-content">Thinking...</div>
          </div>
        )}
      </div>
      <Form.Control
        type="text"
        placeholder="Type your message..."
        className="mt-2"
        value={inputValue}
        onChange={(e) => setInputValue(e.target.value)}
        onKeyDown={handleKeyPress}
        disabled={isLoading}
      />
    </div>
  );
};

export default ChatComponent; 