export interface DocumentTypeInfo {
  count: number;
  selected: boolean;
}

export interface SelectedDocumentsState {
  selectedIndices: Set<number>;
  selectedTexts: string[];
  documentTypes: Map<string, DocumentTypeInfo>;
} 