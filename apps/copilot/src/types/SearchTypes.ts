export interface DocumentInfo {
  title: string;
  citationCount: number;
  documentType: string;
  uri?: string;
  citations: Citation[];
}

export interface Citation {
  content: {
    text: string;
  };
  score: number;
  metadata: {
    'x-amz-kendra-document-title'?: string;
    'x-amz-kendra-score-confidence'?: string;
    '_category'?: string;
    title?: string;
  };
  location?: {
    kendraDocumentLocation?: {
      uri: string;
    };
  };
}

export interface DocumentTypeInfo {
  count: number;
  selected: boolean;
}

export interface SearchState {
  documents: Map<string, DocumentInfo>;
  documentTypes: Map<string, DocumentTypeInfo>;
} 