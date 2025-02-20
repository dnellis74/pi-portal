import { BedrockAgentRuntimeClient, RetrieveCommand } from '@aws-sdk/client-bedrock-agent-runtime';
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

class BedrockService {
  private agentClient: BedrockAgentRuntimeClient;
  private runtimeClient: BedrockRuntimeClient;
  private knowledgeBaseId: string;

  constructor(knowledgeBaseId: string) {
    this.agentClient = new BedrockAgentRuntimeClient(awsConfig);
    this.runtimeClient = new BedrockRuntimeClient(awsConfig);
    this.knowledgeBaseId = knowledgeBaseId;
    console.log('BedrockService constructor accessKey', awsConfig.credentials.accessKeyId);
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

  async sendChatMessage(messages: ChatMessage[], context?: string[]): Promise<string> {
    try {
      console.log('Chat context:', context);
      let systemPrompt = "You are a helpful assistant.";
      if (context && context.length > 0) {
        systemPrompt = `You are a helpful assistant. Use the following context to inform your responses:

Context:

====
${context.join('\n\n')}
====

Remember to use this context to provide accurate and relevant information while maintaining a natural conversation.`;
      }

      const modifiedMessages = [...messages];
      if (modifiedMessages[0]?.role === 'user') {
        modifiedMessages[0] = {
          role: 'user',
          content: `${systemPrompt}\n\n${modifiedMessages[0].content}`
        };
      } else {
        modifiedMessages.unshift({
          role: 'user',
          content: systemPrompt
        });
      }

      const claudeMessages = modifiedMessages.map(msg => ({
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
      console.log('Chat completion payload:', JSON.stringify(payload, null, 2));

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