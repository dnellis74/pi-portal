import { Form } from 'react-bootstrap';
import { useState, useEffect } from 'react';
import { Citation, bedrockService } from '../services/BedrockService';
import { SelectedDocumentsState, DocumentTypeInfo } from '../types/SearchTypes';
import DocumentTypeFilters from './DocumentTypeFilters';

interface SearchResultProps {
  citation: Citation;
  index: number;
  isSelected: boolean;
  onSelect: (index: number, checked: boolean) => void;
}

const SearchResult = ({ citation, index, isSelected, onSelect }: SearchResultProps) => {
  const metadata = citation.metadata || {};
  const content = citation.content || { text: 'No content available' };
  const location = citation.location?.kendraDocumentLocation?.uri || '#';

  return (
    <li className="search-result-item">
      <Form.Check
        type="checkbox"
        id={`citation-${index}`}
        checked={isSelected}
        onChange={(e) => onSelect(index, e.target.checked)}
        label={
          <div>
            <div className="fw-bold">
              {metadata['x-amz-kendra-document-title'] || metadata.title || 'Untitled Document'}
            </div>
            <div className="text-muted small">
              <span>Relevance: {(citation.score * 100).toFixed(1)}% ({metadata['x-amz-kendra-score-confidence'] || 'N/A'})</span>
              <span className="ms-2">Doc Type: {metadata._category || 'Uncategorized'}</span>
            </div>
            <div className="mt-2 text-muted">
              {content.text}
            </div>
            {location !== '#' && (
              <div className="mt-2 small">
                <a href={location} target="_blank" rel="noopener noreferrer">
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
  setSelectedText: (text: string[]) => void;
  setDocumentTypes: (types: Map<string, DocumentTypeInfo>) => void;
  documentTypes: Map<string, DocumentTypeInfo>;
}

const SearchComponent = ({ setSelectedText, setDocumentTypes, documentTypes }: SearchComponentProps) => {
  const [searchResults, setSearchResults] = useState<Citation[]>([]);
  const [isSearching, setIsSearching] = useState(false);
  const [selectedDocs, setSelectedDocs] = useState<SelectedDocumentsState>({
    selectedIndices: new Set<number>(),
    selectedTexts: [],
    documentTypes: new Map<string, DocumentTypeInfo>()
  });

  useEffect(() => {
    // Update selected documents when document types change
    const newSelectedIndices = new Set(selectedDocs.selectedIndices);
    
    // Find all documents of each type and update their selection state
    searchResults.forEach((citation, index) => {
      const docType = citation.metadata?._category || 'Uncategorized';
      const typeInfo = documentTypes.get(docType);
      
      // Only update selection if this document's type exists in documentTypes (was changed)
      if (documentTypes.has(docType)) {
        if (typeInfo?.selected) {
          newSelectedIndices.add(index);
        } else {
          newSelectedIndices.delete(index);
        }
      }
    });

    const newSelectedTexts = Array.from(newSelectedIndices)
      .map(idx => searchResults[idx].content.text);

    setSelectedDocs({
      selectedIndices: newSelectedIndices,
      selectedTexts: newSelectedTexts,
      documentTypes: selectedDocs.documentTypes
    });
    setSelectedText(newSelectedTexts);
  }, [documentTypes, searchResults]);

  const updateDocumentTypesFromResults = (citations: Citation[]) => {
    const types = new Map<string, DocumentTypeInfo>();
    citations.forEach(citation => {
      const docType = citation.metadata?._category || 'Uncategorized';
      const currentInfo = types.get(docType);
      types.set(docType, {
        count: (currentInfo?.count || 0) + 1,
        selected: false
      });
    });
    setDocumentTypes(types);
  };

  const handleSearch = async (searchTerm: string) => {
    if (!searchTerm.trim()) {
      setSearchResults([]);
      setSelectedDocs({
        selectedIndices: new Set<number>(),
        selectedTexts: [],
        documentTypes: new Map<string, DocumentTypeInfo>()
      });
      setSelectedText([]);
      setDocumentTypes(new Map());
      return;
    }
    
    setIsSearching(true);
    try {
      const citations = await bedrockService.searchDocuments(searchTerm);
      setSearchResults(citations);
      updateDocumentTypesFromResults(citations);
      // Clear selections when new search is performed
      setSelectedDocs({
        selectedIndices: new Set<number>(),
        selectedTexts: [],
        documentTypes: new Map<string, DocumentTypeInfo>()
      });
      setSelectedText([]);
    } catch (error) {
      console.error('Error searching Knowledge Base:', error);
      setSearchResults([]);
      setSelectedDocs({
        selectedIndices: new Set<number>(),
        selectedTexts: [],
        documentTypes: new Map<string, DocumentTypeInfo>()
      });
      setSelectedText([]);
      setDocumentTypes(new Map());
    } finally {
      setIsSearching(false);
    }
  };

  const handleCitationSelect = (index: number, checked: boolean) => {
    const citation = searchResults[index];
    
    const newSelectedDocs = { ...selectedDocs };
    const newSelectedIndices = new Set(newSelectedDocs.selectedIndices);

    if (checked) {
      newSelectedIndices.add(index);
    } else {
      newSelectedIndices.delete(index);
    }

    // Update selected texts
    const newSelectedTexts = Array.from(newSelectedIndices)
      .map(idx => searchResults[idx].content.text);

    const updatedSelectedDocs = {
      selectedIndices: newSelectedIndices,
      selectedTexts: newSelectedTexts,
      documentTypes: selectedDocs.documentTypes
    };

    setSelectedDocs(updatedSelectedDocs);
    setSelectedText(newSelectedTexts);
  };

  return (
    <div className="search-column">
      <h4>Document Search</h4>
      <input
        id="search-input"
        type="text"
        placeholder="Search documents..."
        className="form-control mt-2"
        onChange={(e) => handleSearch(e.target.value)}
      />
      <div className="search-results">
        {isSearching ? (
          <p>Searching...</p>
        ) : searchResults.length > 0 ? (
          <ul className="list-unstyled">
            {searchResults.map((citation, index) => (
              <SearchResult
                key={index}
                citation={citation}
                index={index}
                isSelected={selectedDocs.selectedIndices.has(index)}
                onSelect={handleCitationSelect}
              />
            ))}
          </ul>
        ) : (
          <p className="text-muted">Enter a search term to see results</p>
        )}
      </div>
    </div>
  );
};

export default SearchComponent; 