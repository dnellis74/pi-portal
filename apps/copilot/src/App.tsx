import { Container, Row, Col, Navbar } from 'react-bootstrap';
import CenterContent from './components/CenterContent';
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
          <CenterContent />
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
