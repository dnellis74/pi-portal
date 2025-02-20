import { Container, Row, Col, Navbar, Form } from 'react-bootstrap';
import './App.css';

function App() {
  return (
    <Container fluid>
      {/* Header */}
      <Navbar bg="dark" variant="dark">
        <Navbar.Brand href="#home">Header</Navbar.Brand>
      </Navbar>

      {/* Main Content */}
      <Row className="flex-grow-1">
        <Col md={2} className="bg-light">
          {/* Left Sidebar */}
          <Row>Filters</Row>
          <Row>Search History</Row>
        </Col>
        <Col md={10}>
          {/* Center Content */}
          <div className="center-content">
            <Row>
              <Col md={6}>
                <div className="search-column">
                  <h4>Document Search</h4>
                  <Form.Control
                    type="text"
                    placeholder="Search documents..."
                    className="mt-2"
                  />
                  <div className="search-results">
                    {/* Search results will be displayed here */}
                    <p className="text-muted">Enter a search term to see results</p>
                  </div>
                </div>
              </Col>
              <Col md={6}>
                <div className="search-column">
                  <h4>Document Chat</h4>
                  <Form.Control
                    type="text"
                    placeholder="How can I help?"
                    className="mt-2"
                  />
                  <div className="chat-results">
                    {/* Chat messages will be displayed here */}
                    <p className="text-muted">Start a conversation by typing a message</p>
                  </div>
                </div>
              </Col>
            </Row>
          </div>
        </Col>
      </Row>

      {/* Footer */}
      <footer className="footer">
        Footer
      </footer>
    </Container>
  );
}

export default App;
