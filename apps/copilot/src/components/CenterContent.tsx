import { Row, Col } from 'react-bootstrap';
import SearchComponent from './SearchComponent';
import ChatComponent from './ChatComponent';
import { DocumentTypeInfo } from '../types/SearchTypes';

interface CenterContentProps {
  selectedText: string[];
  setSelectedText: (text: string[]) => void;
  setDocumentTypes: (types: Map<string, DocumentTypeInfo>) => void;
  onTypeSelect: (type: string, selected: boolean) => void;
  documentTypes: Map<string, DocumentTypeInfo>;
}

const CenterContent = ({ selectedText, setSelectedText, setDocumentTypes, onTypeSelect, documentTypes }: CenterContentProps) => {
  return (
    <div className="center-content">
      <Row>
        <Col md={6}>
          <SearchComponent 
            setSelectedText={setSelectedText} 
            setDocumentTypes={setDocumentTypes}
            onTypeSelect={onTypeSelect}
            documentTypes={documentTypes}
          />
        </Col>
        <Col md={6}>
          <ChatComponent selectedText={selectedText} />
        </Col>
      </Row>
    </div>
  );
};

export default CenterContent; 