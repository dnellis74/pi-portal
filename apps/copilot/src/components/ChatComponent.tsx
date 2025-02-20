import { Form } from 'react-bootstrap';

const ChatComponent = () => {
  return (
    <div className="search-column">
      <h4>Document Chat</h4>
      <Form.Control
        type="text"
        placeholder="How can I help?"
        className="mt-2"
      />
      <div className="chat-results">
        <p className="text-muted">Start a conversation by typing a message</p>
      </div>
    </div>
  );
};

export default ChatComponent; 