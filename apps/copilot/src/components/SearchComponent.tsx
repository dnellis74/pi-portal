import { useState } from 'react';
import { Citation, bedrockService } from '../services/BedrockService';
import { DocumentTypeInfo, SearchState, DocumentInfo } from '../types/SearchTypes';

interface DocumentResultProps {
  document: DocumentInfo;
}

const DocumentResult = ({ document }: DocumentResultProps) => {
  return (
    <li className="search-result-item">
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
    </li>
  );
};

interface SearchComponentProps {
  setDocumentTypes: (types: Map<string, DocumentTypeInfo>) => void;
  documentTypes: Map<string, DocumentTypeInfo>;
}

const SearchComponent = ({ setDocumentTypes, documentTypes }: SearchComponentProps) => {
  const [searchState, setSearchState] = useState<SearchState>({
    documents: new Map<string, DocumentInfo>(),
    documentTypes: new Map<string, DocumentTypeInfo>()
  });
  const [isSearching, setIsSearching] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');

  const processSearchResults = (citations: Citation[]) => {
    const documents = new Map<string, DocumentInfo>();
    const types = new Map<string, DocumentTypeInfo>();
    const docTypeCount = new Map<string, Set<string>>();

    citations.forEach(citation => {
      const docTitle = citation.metadata['x-amz-kendra-document-title'] || 
                      citation.metadata.title || 
                      'Untitled Document';
      const docType = citation.metadata._category || 'Uncategorized';
      const uri = citation.location?.kendraDocumentLocation?.uri;

      // Update document info
      const existingDoc = documents.get(docTitle);
      if (existingDoc) {
        existingDoc.citationCount++;
        existingDoc.citations.push(citation);
        documents.set(docTitle, existingDoc);
      } else {
        documents.set(docTitle, {
          title: docTitle,
          citationCount: 1,
          documentType: docType,
          uri: uri,
          citations: [citation]
        });

        // Track unique documents per type
        if (!docTypeCount.has(docType)) {
          docTypeCount.set(docType, new Set());
        }
        docTypeCount.get(docType)?.add(docTitle);
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

  const handleSearch = async (searchTerm: string) => {
    if (!searchTerm.trim()) {
      setSearchState({
        documents: new Map(),
        documentTypes: new Map()
      });
      setDocumentTypes(new Map());
      return;
    }
    
    setIsSearching(true);
    try {
      const citations = await bedrockService.searchDocuments(searchTerm);
      processSearchResults(citations);
    } catch (error) {
      console.error('Error searching Knowledge Base:', error);
      setSearchState({
        documents: new Map(),
        documentTypes: new Map()
      });
      setDocumentTypes(new Map());
    } finally {
      setIsSearching(false);
    }
  };

  return (
    <div className="search-column">
      <h4>Document Search</h4>
      <input
        id="search-input"
        type="text"
        placeholder="Press enter to search documents..."
        className="form-control mt-2"
        value={searchTerm}
        onChange={(e) => setSearchTerm(e.target.value)}
        onKeyDown={(e) => {
          if (e.key === 'Enter') {
            handleSearch(searchTerm);
          }
        }}
      />
      <div className="search-results">
        {isSearching ? (
          <p>Searching...</p>
        ) : searchState.documents.size > 0 ? (
          <ul className="list-unstyled">
            {(() => {
              const hasSelectedTypes = Array.from(documentTypes.values()).some(info => info.selected);
              const visibleDocuments = Array.from(searchState.documents.values()).filter(doc => {
                return !hasSelectedTypes || documentTypes.get(doc.documentType)?.selected;
              });

              return visibleDocuments.map((document, index) => (
                <DocumentResult
                  key={index}
                  document={document}
                />
              ));
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