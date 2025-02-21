import React from 'react';
import { Form } from 'react-bootstrap';
import { DocumentTypeInfo } from '../types/SearchTypes';

interface DocumentTypeFiltersProps {
  documentTypes: Map<string, DocumentTypeInfo>;
  onTypeSelect: (type: string, selected: boolean) => void;
}

const DocumentTypeFilters: React.FC<DocumentTypeFiltersProps> = ({ documentTypes, onTypeSelect }) => {
  return (
    <div>
      <h6>Document Types</h6>
      <ul className="list-unstyled">
        {Array.from(documentTypes.entries()).map(([type, info]) => (
          <li key={type} className="mb-1">
            <Form.Check
              type="checkbox"
              id={`filter-${type}`}
              checked={info.selected}
              label={`${type} (${info.count})`}
              onChange={(e) => onTypeSelect(type, e.target.checked)}
            />
          </li>
        ))}
      </ul>
    </div>
  );
};

export default DocumentTypeFilters; 