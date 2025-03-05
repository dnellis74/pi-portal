import { Form, Button, InputGroup } from 'react-bootstrap';
import { useState, useEffect } from 'react';
import { Citation, bedrockService } from '../services/BedrockService';
import { DocumentTypeInfo, SearchState, DocumentInfo, SelectedDocument } from '../types/SearchTypes';

interface DocumentResultProps {
  document: DocumentInfo;
  onSelect: (uri: string, selected: boolean) => void;
}

const DocumentResult = ({ document, onSelect }: DocumentResultProps) => {
  return (
    <li className="search-result-item">
      <Form.Check
        type="checkbox"
        id={`doc-${document.uri}`}
        checked={document.selected || false}
        onChange={(e) => document.uri && onSelect(document.uri, e.target.checked)}
        label={
          <div>
            <div className="fw-bold">
              {document.title}
            </div>
            <div className="text-muted small">
              <span>Document Type: {document.documentType}</span>
              <span className="ms-2">Citations: {document.citationCount}</span>
            </div>
            {document.uri && (
              <div className="mt-2 small">
                <a href={document.uri} target="_blank" rel="noopener noreferrer">
                  View Document
                </a>
              </div>
            )}
          </div>
        }
      />
    </li>
  );
};

interface SearchComponentProps {
  setDocumentTypes: (types: Map<string, DocumentTypeInfo>) => void;
  documentTypes: Map<string, DocumentTypeInfo>;
  onSelectedDocumentsChange: (documents: SelectedDocument[]) => void;
  selectedDocuments: SelectedDocument[];
  onGeneratedContent: (content: string) => void;
}

const SearchComponent = ({ 
  setDocumentTypes, 
  documentTypes, 
  onSelectedDocumentsChange,
  selectedDocuments,
  onGeneratedContent
}: SearchComponentProps) => {
  const [searchState, setSearchState] = useState<SearchState>({
    documents: new Map<string, DocumentInfo>(),
    documentTypes: new Map<string, DocumentTypeInfo>()
  });
  const [selectedDocumentMap, setSelectedDocumentMap] = useState<Map<string, DocumentInfo>>(new Map());
  const [isSearching, setIsSearching] = useState(false);
  const [isGenerating, setIsGenerating] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [generatedResult, setGeneratedResult] = useState<string | null>(null);

  // Initialize and update selectedDocumentMap when selectedDocuments changes
  useEffect(() => {
    const newMap = new Map(selectedDocumentMap);
    selectedDocuments.forEach(doc => {
      if (!newMap.has(doc.uri)) {
        newMap.set(doc.uri, {
          title: doc.title,
          documentType: doc.documentType,
          uri: doc.uri,
          citationCount: 0,
          citations: [],
          selected: true
        });
      }
    });
    setSelectedDocumentMap(newMap);
  }, [selectedDocuments]);

  const handleDocumentSelect = (uri: string, selected: boolean) => {
    // Update documents in state to reflect selection
    const newDocuments = new Map(searchState.documents);
    const doc = newDocuments.get(uri) || selectedDocumentMap.get(uri);
    
    if (doc) {
      const updatedDoc = { ...doc, selected };
      newDocuments.set(uri, updatedDoc);
      
      if (selected) {
        // Add to selectedDocumentMap if selected
        setSelectedDocumentMap(new Map(selectedDocumentMap).set(uri, updatedDoc));
      } else {
        // Remove from selectedDocumentMap if unselected
        const newSelectedMap = new Map(selectedDocumentMap);
        newSelectedMap.delete(uri);
        setSelectedDocumentMap(newSelectedMap);
      }

      setSearchState({
        ...searchState,
        documents: newDocuments
      });
    }

    // Notify parent of selected documents
    const newSelectedDocs: SelectedDocument[] = Array.from(newDocuments.values())
      .filter(doc => doc.selected && doc.uri)
      .map(doc => ({
        uri: doc.uri!,
        documentType: doc.documentType,
        title: doc.title
      }));

    onSelectedDocumentsChange(newSelectedDocs);
  };

  const processSearchResults = (citations: Citation[]) => {
    const documents = new Map<string, DocumentInfo>();
    const types = new Map<string, DocumentTypeInfo>();
    const docTypeCount = new Map<string, Set<string>>();

    // First, add all selected documents to ensure they're always present
    selectedDocumentMap.forEach((doc, uri) => {
      documents.set(uri, { ...doc });
      const docType = doc.documentType;
      if (!docTypeCount.has(docType)) {
        docTypeCount.set(docType, new Set([uri]));
      } else {
        docTypeCount.get(docType)?.add(uri);
      }
    });

    citations.forEach(citation => {
      const docTitle = citation.metadata['x-amz-kendra-document-title'] || 
                      citation.metadata.title || 
                      'Untitled Document';
      const docType = citation.metadata._category || 'Uncategorized';
      const uri = citation.location?.kendraDocumentLocation?.uri;

      if (!uri) return; // Skip documents without URI

      // Update document info
      const existingDoc = documents.get(uri);
      if (existingDoc) {
        existingDoc.citationCount++;
        existingDoc.citations.push(citation);
        documents.set(uri, existingDoc);
      } else {
        documents.set(uri, {
          title: docTitle,
          citationCount: 1,
          documentType: docType,
          uri: uri,
          citations: [citation],
          selected: selectedDocumentMap.has(uri)
        });

        // Track unique documents per type
        if (!docTypeCount.has(docType)) {
          docTypeCount.set(docType, new Set());
        }
        docTypeCount.get(docType)?.add(uri);
      }
    });

    // Set document type counts based on unique documents
    docTypeCount.forEach((docs, docType) => {
      types.set(docType, {
        count: docs.size,
        selected: documentTypes.get(docType)?.selected || false
      });
    });

    setSearchState({
      documents,
      documentTypes: types
    });
    setDocumentTypes(types);
  };

  const clearSearch = () => {
    setSearchTerm('');
    
    // When clearing search, show only selected documents
    const documents = new Map<string, DocumentInfo>();
    const types = new Map<string, DocumentTypeInfo>();
    const docTypeCount = new Map<string, Set<string>>();

    // Add all selected documents
    selectedDocumentMap.forEach((doc, uri) => {
      documents.set(uri, { ...doc });
      const docType = doc.documentType;
      if (!docTypeCount.has(docType)) {
        docTypeCount.set(docType, new Set([uri]));
      } else {
        docTypeCount.get(docType)?.add(uri);
      }
    });

    // Update document type counts
    docTypeCount.forEach((docs, docType) => {
      types.set(docType, {
        count: docs.size,
        selected: documentTypes.get(docType)?.selected || false
      });
    });

    setSearchState({
      documents,
      documentTypes: types
    });
    setDocumentTypes(types);
  };

  const handleSearch = async (searchTerm: string) => {
    if (!searchTerm.trim()) {
      clearSearch();
      return;
    }
    
    setIsSearching(true);
    try {
      const citations = await bedrockService.searchDocuments(searchTerm);
      processSearchResults(citations);
    } catch (error) {
      console.error('Error searching Knowledge Base:', error);
      // On error, show selected documents
      clearSearch();
    } finally {
      setIsSearching(false);
    }
  };

  const handleGenerate = async () => {
    const selectedUrls = Array.from(selectedDocumentMap.values())
      .filter(doc => doc.uri)
      .map(doc => doc.uri!);

    if (selectedUrls.length === 0) {
      return;
    }

    setIsGenerating(true);

    try {
      const result = await bedrockService.generateFromDocuments(selectedUrls);
      onGeneratedContent(result);
    } catch (error) {
      console.error('Error generating from documents:', error);
    } finally {
      setIsGenerating(false);
    }
  };

  return (
    <div className="search-column">
      <h4>Document Search</h4>
      <div className="mb-3">
        <InputGroup>
          <Form.Control
            id="search-input"
            type="text"
            placeholder="Enter search term..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter') {
                handleSearch(searchTerm);
              }
            }}
          />
          <Button 
            variant="outline-secondary" 
            onClick={() => clearSearch()}
          >
            Clear
          </Button>
          <Button 
            variant="primary" 
            onClick={() => handleSearch(searchTerm)}
            disabled={isSearching}
          >
            {isSearching ? 'Searching...' : 'Search'}
          </Button>
        </InputGroup>
      </div>

      {selectedDocumentMap.size > 0 && (
        <div className="mb-3 d-flex justify-content-between align-items-center">
          <span className="text-muted">
            {selectedDocumentMap.size} document{selectedDocumentMap.size !== 1 ? 's' : ''} selected
          </span>
          <Button
            variant="success"
            onClick={handleGenerate}
            disabled={isGenerating}
          >
            {isGenerating ? 'Generating...' : 'Generate from Selected Documents'}
          </Button>
        </div>
      )}

      {generatedResult && (
        <div className="mb-3 p-3 bg-light border rounded">
          <h6>Generated Result:</h6>
          <div className="text-muted">{generatedResult}</div>
        </div>
      )}

      <div className="search-results">
        {isSearching ? (
          <p>Searching...</p>
        ) : searchState.documents.size > 0 ? (
          <ul className="list-unstyled">
            {(() => {
              const allDocuments = Array.from(searchState.documents.values());
              const hasSelectedTypes = Array.from(documentTypes.values()).some(info => info.selected);
              
              // Split documents into selected and unselected
              const selectedDocs = allDocuments.filter(doc => doc.selected)
                .sort((a, b) => a.title.localeCompare(b.title));

              const unselectedFilteredDocs = allDocuments
                .filter(doc => !doc.selected && (!hasSelectedTypes || documentTypes.get(doc.documentType)?.selected))
                .sort((a, b) => a.title.localeCompare(b.title));

              // If we have selected documents, show a section header
              return (
                <>
                  {selectedDocs.length > 0 && (
                    <>
                      <li className="mb-2">
                        <h6 className="text-muted">Selected Documents</h6>
                      </li>
                      {selectedDocs.map((document) => (
                        <DocumentResult
                          key={document.uri}
                          document={document}
                          onSelect={handleDocumentSelect}
                        />
                      ))}
                    </>
                  )}
                  {unselectedFilteredDocs.length > 0 && (
                    <>
                      <li className="mt-4 mb-2">
                        <h6 className="text-muted">Search Results</h6>
                      </li>
                      {unselectedFilteredDocs.map((document) => (
                        <DocumentResult
                          key={document.uri}
                          document={document}
                          onSelect={handleDocumentSelect}
                        />
                      ))}
                    </>
                  )}
                </>
              );
            })()}
          </ul>
        ) : (
          <p className="text-muted">Enter a search term to see results</p>
        )}
      </div>
    </div>
  );
};

export default SearchComponent; 