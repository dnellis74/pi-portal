import { Form } from 'react-bootstrap';
import { useState } from 'react';
import { Citation, bedrockService } from '../services/BedrockService';

const SearchComponent = () => {
  const [searchResults, setSearchResults] = useState<Citation[]>([]);
  const [isSearching, setIsSearching] = useState(false);

  const handleSearch = async (searchTerm: string) => {
    if (!searchTerm.trim()) return;
    
    setIsSearching(true);
    try {
      const citations = await bedrockService.searchDocuments(searchTerm);
      setSearchResults(citations);
    } catch (error) {
      console.error('Error searching Knowledge Base:', error);
      setSearchResults([]);
    } finally {
      setIsSearching(false);
    }
  };

  const renderCitation = (citation: Citation, index: number) => {
    const metadata = citation.metadata || {};
    const content = citation.content || { text: 'No content available' };
    const location = citation.location?.kendraDocumentLocation?.uri || '#';

    return (
      <li key={index} className="mb-2 p-2 border-bottom">
        <div className="fw-bold">
          {metadata['x-amz-kendra-document-title'] || metadata.title || 'Untitled Document'}
        </div>
        <div className="text-muted small">
          <span>Relevance: {(citation.score * 100).toFixed(1)}% ({metadata['x-amz-kendra-score-confidence'] || 'N/A'})</span>
          <span className="ms-2">Category: {metadata._category || 'Uncategorized'}</span>
        </div>
        {/* <div className="mt-1">{content.text}</div> --> */}
        {location !== '#' && (
          <div className="mt-2 small">
            <a href={location} target="_blank" rel="noopener noreferrer">
              View Document
            </a>
          </div>
        )}
      </li>
    );
  };

  return (
    <div className="search-column">
      <h4>Document Search</h4>
      <Form.Control
        id="search-input"
        type="text"
        placeholder="Search documents..."
        className="mt-2"
        onChange={(e) => handleSearch(e.target.value)}
      />
      <div className="search-results">
        {isSearching ? (
          <p>Searching...</p>
        ) : searchResults.length > 0 ? (
          <ul className="list-unstyled">
            {searchResults.map(renderCitation)}
          </ul>
        ) : (
          <p className="text-muted">Enter a search term to see results</p>
        )}
      </div>
    </div>
  );
};

export default SearchComponent; 