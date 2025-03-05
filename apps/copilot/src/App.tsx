import { Container, Row, Col, Navbar } from 'react-bootstrap';
import { useState } from 'react';
import SearchComponent from './components/SearchComponent';
import ChatComponent from './components/ChatComponent';
import DocumentTypeFilters from './components/DocumentTypeFilters';
import { DocumentTypeInfo, SelectedDocument } from './types/SearchTypes';
import { ChatMessage } from './services/BedrockService';
import './App.css';

function App() {
  const [documentTypes, setDocumentTypes] = useState<Map<string, DocumentTypeInfo>>(new Map());
  const [selectedDocuments, setSelectedDocuments] = useState<SelectedDocument[]>([]);
  const [messages, setMessages] = useState<ChatMessage[]>([]);

  const handleTypeSelect = (type: string, selected: boolean) => {
    const newTypes = new Map(documentTypes);
    const typeInfo = newTypes.get(type);
    if (typeInfo) {
      newTypes.set(type, { ...typeInfo, selected });
      setDocumentTypes(newTypes);
    }
  };

  const handleSelectedDocumentsChange = (documents: SelectedDocument[]) => {
    setSelectedDocuments(documents);
  };

  const handleGeneratedContent = (content: string) => {
    const newMessage: ChatMessage = {
      role: 'assistant',
      content: content
    };
    setMessages(prev => [...prev, newMessage]);
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
          <DocumentTypeFilters documentTypes={documentTypes} onTypeSelect={handleTypeSelect} />
        </Col>
        <Col md={10}>
          {/* Center Content */}
          <Row>
            <Col md={6}>
              <SearchComponent 
                setDocumentTypes={setDocumentTypes}
                documentTypes={documentTypes}
                onSelectedDocumentsChange={handleSelectedDocumentsChange}
                selectedDocuments={selectedDocuments}
                onGeneratedContent={handleGeneratedContent}
              />
            </Col>
            <Col md={6}>
              <ChatComponent 
                messages={messages}
                setMessages={setMessages}
              />
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
