import { Row, Col } from 'react-bootstrap';
import SearchComponent from './SearchComponent';
import ChatComponent from './ChatComponent';

interface CenterContentProps {
  selectedText: string[];
  setSelectedText: (text: string[]) => void;
}

const CenterContent = ({ selectedText, setSelectedText }: CenterContentProps) => {
  return (
    <div className="center-content">
      <Row>
        <Col md={6}>
          <SearchComponent setSelectedText={setSelectedText} />
        </Col>
        <Col md={6}>
          <ChatComponent selectedText={selectedText} />
        </Col>
      </Row>
    </div>
  );
};

export default CenterContent; 