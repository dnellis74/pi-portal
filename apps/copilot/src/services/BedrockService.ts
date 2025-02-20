import { BedrockAgentRuntimeClient, RetrieveCommand } from '@aws-sdk/client-bedrock-agent-runtime';
import { awsConfig, bedrockConfig } from '../config/aws-config';

interface DocumentMetadata {
  '_source_uri': string;
  'x-amz-kendra-score-confidence': 'HIGH' | 'MEDIUM' | 'LOW';
  'x-amz-kendra-document-title': string;
  'jurisdiction': string;
  'description': string;
  '_category': string;
  'title': string;
}

interface DocumentContent {
  text: string;
  type: string;
}

interface DocumentLocation {
  kendraDocumentLocation: {
    uri: string;
  };
  type: string;
}

export interface Citation {
  content: DocumentContent;
  location: DocumentLocation;
  metadata: DocumentMetadata;
  score: number;
}

class BedrockService {
  private client: BedrockAgentRuntimeClient;
  private knowledgeBaseId: string;

  constructor(knowledgeBaseId: string) {
    this.client = new BedrockAgentRuntimeClient(awsConfig);
    this.knowledgeBaseId = knowledgeBaseId;
  }

  async searchDocuments(searchTerm: string): Promise<Citation[]> {
    try {
      const command = new RetrieveCommand({
        knowledgeBaseId: this.knowledgeBaseId,
        retrievalQuery: { text: searchTerm },
        retrievalConfiguration: {
          vectorSearchConfiguration: {
            numberOfResults: 5
          }
        }
      });

      const response = await this.client.send(command);
      return response.retrievalResults?.map(result => ({
        content: result.content as DocumentContent,
        location: result.location as DocumentLocation,
        metadata: result.metadata as DocumentMetadata,
        score: result.score || 0
      })) || [];
    } catch (error) {
      console.error('Error searching Knowledge Base:', error);
      throw error;
    }
  }
}

export const bedrockService = new BedrockService(bedrockConfig.knowledgeBaseId);
export default BedrockService; 