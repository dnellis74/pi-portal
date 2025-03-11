import { BedrockAgentRuntimeClient, RetrieveCommand, RetrieveAndGenerateCommand } from '@aws-sdk/client-bedrock-agent-runtime';
import { BedrockRuntimeClient, InvokeModelCommand } from '@aws-sdk/client-bedrock-runtime';
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

export interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
}

export class BedrockService {
  private agentClient: BedrockAgentRuntimeClient;
  private runtimeClient: BedrockRuntimeClient;
  private knowledgeBaseId: string;

  constructor(knowledgeBaseId: string) {
    this.agentClient = new BedrockAgentRuntimeClient(awsConfig);
    this.runtimeClient = new BedrockRuntimeClient(awsConfig);
    this.knowledgeBaseId = knowledgeBaseId;
  }

  async searchDocuments(searchTerm: string): Promise<Citation[]> {
    try {
      const command = new RetrieveCommand({
        knowledgeBaseId: this.knowledgeBaseId,
        retrievalQuery: { text: searchTerm },
        retrievalConfiguration: {
          vectorSearchConfiguration: {
            numberOfResults: 100
          }
        }
      });

      const response = await this.agentClient.send(command);
      return response.retrievalResults?.map(result => ({
        content: result.content as DocumentContent,
        location: result.location as DocumentLocation,
        metadata: result.metadata as unknown as DocumentMetadata,
        score: result.score || 0
      })) || [];
    } catch (error) {
      console.error('Error searching Knowledge Base:', error);
      throw error;
    }
  }

  async generateFromDocuments(documentUrls: string[], searchQuery: string): Promise<string> {
    try {
      const orAllFilters = documentUrls.map(url => ({
        equals: {
          key: "pi_url",
          value: url
        }
      }));

      const command = new RetrieveAndGenerateCommand({
        input: {
          text: searchQuery
        },
        retrieveAndGenerateConfiguration: {
          type: "KNOWLEDGE_BASE",
          knowledgeBaseConfiguration: {
            knowledgeBaseId: this.knowledgeBaseId,
            modelArn: "anthropic.claude-3-5-sonnet-20240620-v1:0",
            retrievalConfiguration: {
              vectorSearchConfiguration: {
                numberOfResults: 100,
                filter: {
                  orAll: orAllFilters
                }
              }
            }
          }
        }
      });

      const response = await this.agentClient.send(command);
      return response.output?.text || 'No response generated';
    } catch (error) {
      console.error('Error in generative call:', error);
      throw error;
    }
  }

  async sendChatMessage(messages: ChatMessage[]): Promise<string> {
    try {
      const claudeMessages = messages.map(msg => ({
        role: msg.role,
        content: [{ type: 'text', text: msg.content }]
      }));

      const payload = {
        anthropic_version: 'bedrock-2023-05-31',
        messages: claudeMessages,
        max_tokens: 2000,
        temperature: 0.7,
        top_p: 0.9,
      };

      const command = new InvokeModelCommand({
        modelId: 'anthropic.claude-3-5-sonnet-20240620-v1:0',
        contentType: 'application/json',
        accept: 'application/json',
        body: JSON.stringify(payload)
      });

      const response = await this.runtimeClient.send(command);
      const responseBody = JSON.parse(new TextDecoder().decode(response.body));
      return responseBody.content[0].text;
    } catch (error) {
      console.error('Error sending chat message:', error);
      throw error;
    }
  }
}

export const bedrockService = new BedrockService(bedrockConfig.knowledgeBaseId);
export default BedrockService; 