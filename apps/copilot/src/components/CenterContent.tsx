import { Row, Col } from 'react-bootstrap';
import SearchComponent from './SearchComponent';
import ChatComponent from './ChatComponent';

const CenterContent = () => {
  return (
    <div className="center-content">
      <Row>
        <Col md={6}>
          <SearchComponent />
        </Col>
        <Col md={6}>
          <ChatComponent />
        </Col>
      </Row>
    </div>
  );
};

export default CenterContent; 