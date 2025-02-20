import { Form } from 'react-bootstrap';
import { useState } from 'react';
import { Citation, bedrockService } from '../services/BedrockService';

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
    <li className="mb-2 p-2 border-bottom">
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
              <span className="ms-2">Category: {metadata._category || 'Uncategorized'}</span>
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
}

const SearchComponent = ({ setSelectedText }: SearchComponentProps) => {
  const [searchResults, setSearchResults] = useState<Citation[]>([]);
  const [isSearching, setIsSearching] = useState(false);
  const [selectedCitations, setSelectedCitations] = useState<Set<number>>(new Set());

  const handleSearch = async (searchTerm: string) => {
    if (!searchTerm.trim()) return;
    
    setIsSearching(true);
    try {
      const citations = await bedrockService.searchDocuments(searchTerm);
      setSearchResults(citations);
      // Clear selections when new search is performed
      setSelectedCitations(new Set());
      setSelectedText([]);
    } catch (error) {
      console.error('Error searching Knowledge Base:', error);
      setSearchResults([]);
      setSelectedCitations(new Set());
      setSelectedText([]);
    } finally {
      setIsSearching(false);
    }
  };

  const handleCitationSelect = (index: number, checked: boolean) => {
    const newSelectedCitations = new Set(selectedCitations);
    if (checked) {
      newSelectedCitations.add(index);
    } else {
      newSelectedCitations.delete(index);
    }
    setSelectedCitations(newSelectedCitations);

    // Update selected text based on selected citations
    const selectedTexts = Array.from(newSelectedCitations).map(idx => searchResults[idx].content.text);
    setSelectedText(selectedTexts);
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
                isSelected={selectedCitations.has(index)}
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