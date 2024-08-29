import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import config from "./config.json";



const SearchComponent: React.FC = () => {
  const [query, setQuery] = useState<string>('');
  const [results, setResults] = useState<any[]>([]);

  const handleSearch = async () => {
    const apiKey = config.azureSearchApiKey;
    const serviceName = 'polint';
    const indexName = 'ai-index';
    const apiVersion = '2016-09-01'; // Use the appropriate API version

    const url = `https://${serviceName}.search.windows.net/indexes/${indexName}/docs?api-version=${apiVersion}&search=${encodeURIComponent(query)}`;

    const response = await fetch(url, {
      headers: {
        'Content-Type': 'application/json',
        'api-key': apiKey,
      },
    });

    if (response.ok) {
      const data = await response.json();
      setResults(data.value);
    } else {
      console.error('Search request failed');
    }
  };

  return (
    <div>
      <input
        type="text"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        placeholder="Search..."
      />
      <button onClick={handleSearch}>Search</button>
      <ul style={{ textAlign: 'left', listStyleType: 'square' }}>
        {results.map((result, index) => (
          <li key={index}><Link to={result.url} target='top'>{result.title}</Link></li> // Adjust based on your document structure
        ))}
      </ul>
    </div>
  );
};

export default SearchComponent;