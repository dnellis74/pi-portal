import { 
  KendraClient, 
  QueryCommand,
  RetrieveCommand
} from "@aws-sdk/client-kendra";
import type { 
  QueryCommandInput,
  QueryResultItem,
  DocumentAttributeValue,
  RetrieveCommandInput,
  AttributeFilter,
  DocumentAttribute,
  RetrieveResultItem,
  TextWithHighlights
} from "@aws-sdk/client-kendra";
import { awsConfig } from '../config/aws-config';

// Validate required environment variables
const requiredEnvVars = {
  VITE_AWS_REGION: import.meta.env.VITE_AWS_REGION,
  VITE_AWS_ACCESS_KEY_ID: import.meta.env.VITE_AWS_ACCESS_KEY_ID,
  VITE_AWS_SECRET_ACCESS_KEY: import.meta.env.VITE_AWS_SECRET_ACCESS_KEY,
  VITE_KENDRA_INDEX_ID: import.meta.env.VITE_KENDRA_INDEX_ID
};

const missingEnvVars = Object.entries(requiredEnvVars)
  .filter(([_, value]) => !value)
  .map(([key]) => key);

if (missingEnvVars.length > 0) {
  throw new Error(
    `Missing required environment variables: ${missingEnvVars.join(', ')}\n` +
    'Please create a .env file in the apps/bob directory with the following variables:\n' +
    'VITE_AWS_REGION=your-aws-region\n' +
    'VITE_AWS_ACCESS_KEY_ID=your-aws-access-key-id\n' +
    'VITE_AWS_SECRET_ACCESS_KEY=your-aws-secret-access-key\n' +
    'VITE_KENDRA_INDEX_ID=your-kendra-index-id'
  );
}

export interface KendraResult {
  id: string;
  title: string;
  excerpt: string;
  uri?: string;
  score: number;
  documentAttributes?: Record<string, DocumentAttributeValue>;
}

export class KendraService {
  private client: KendraClient;
  private indexId: string;

  constructor(indexId: string) {
    this.client = new KendraClient(awsConfig);
    this.indexId = indexId;
  }

  async query(queryText: string): Promise<KendraResult[]> {
    try {
      const input: QueryCommandInput = {
        IndexId: this.indexId,
        QueryText: queryText,
        PageSize: 10,
        AttributeFilter: {
          EqualsTo: {
            Key: "_language_code",
            Value: {
              StringValue: "en"
            }
          }
        } as AttributeFilter
      };

      const command = new QueryCommand(input);
      const response = await this.client.send(command);

      return (response.ResultItems || []).map(item => this.mapQueryResultItem(item));
    } catch (error) {
      console.error('Error querying Kendra:', error);
      throw error;
    }
  }

  async retrieve(documentIds: string[]): Promise<KendraResult[]> {
    try {
      const input: RetrieveCommandInput = {
        IndexId: this.indexId,
        QueryText: documentIds.join(' '),
        PageSize: 10,
        AttributeFilter: {
          EqualsTo: {
            Key: "_document_id",
            Value: {
              StringListValue: documentIds
            }
          }
        } as AttributeFilter
      };

      const command = new RetrieveCommand(input);
      const response = await this.client.send(command);

      return (response.ResultItems || []).map(item => this.mapRetrieveResultItem(item));
    } catch (error) {
      console.error('Error retrieving from Kendra:', error);
      throw error;
    }
  }

  private mapQueryResultItem(item: QueryResultItem): KendraResult {
    const score = item.ScoreAttributes?.ScoreConfidence;
    return {
      id: item.DocumentId || '',
      title: item.DocumentTitle?.Text || '',
      excerpt: item.DocumentExcerpt?.Text || '',
      uri: item.DocumentURI,
      score: typeof score === 'number' ? score : 0,
      documentAttributes: item.DocumentAttributes?.reduce((acc: Record<string, DocumentAttributeValue>, attr: DocumentAttribute) => {
        if (attr.Key && attr.Value) {
          acc[attr.Key] = attr.Value;
        }
        return acc;
      }, {})
    };
  }

  private mapRetrieveResultItem(item: RetrieveResultItem): KendraResult {
    return {
      id: item.DocumentId || '',
      title: typeof item.DocumentTitle === 'string' ? item.DocumentTitle : '',
      excerpt: typeof item.Content === 'string' ? item.Content : '',
      uri: item.DocumentURI,
      score: typeof item.ScoreAttributes?.ScoreConfidence === 'number' ? item.ScoreAttributes.ScoreConfidence : 0,
      documentAttributes: item.DocumentAttributes?.reduce((acc: Record<string, DocumentAttributeValue>, attr: DocumentAttribute) => {
        if (attr.Key && attr.Value) {
          acc[attr.Key] = attr.Value;
        }
        return acc;
      }, {})
    };
  }
}

// Export a default instance with the index ID from environment variables
export const kendraService = new KendraService(import.meta.env.VITE_KENDRA_INDEX_ID || '');
export default KendraService; 