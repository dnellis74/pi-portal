import { Container, Row, Col, Navbar } from 'react-bootstrap';
import { useState } from 'react';
import SearchComponent from './components/SearchComponent';
import ChatComponent from './components/ChatComponent';
import DocumentTypeFilters from './components/DocumentTypeFilters';
import { DocumentTypeInfo } from './types/SearchTypes';
import './App.css';

function App() {
  const [documentTypes, setDocumentTypes] = useState<Map<string, DocumentTypeInfo>>(new Map());

  const handleTypeSelect = (type: string, selected: boolean) => {
    const newTypes = new Map(documentTypes);
    const typeInfo = newTypes.get(type);
    if (typeInfo) {
      newTypes.set(type, { ...typeInfo, selected });
      setDocumentTypes(newTypes);
    }
  };

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
          <Row><DocumentTypeFilters documentTypes={documentTypes} onTypeSelect={handleTypeSelect} /></Row>            
          <Row>Search History</Row>
        </Col>
        <Col md={10}>
          {/* Center Content */}
          <Row>
            <Col md={6}>
              <SearchComponent 
                setDocumentTypes={setDocumentTypes}
                documentTypes={documentTypes}
              />
            </Col>
            <Col md={6}>
              <ChatComponent />
            </Col>
          </Row>
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
