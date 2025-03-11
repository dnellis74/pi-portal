export const awsConfig = {
  region: import.meta.env.VITE_AWS_REGION || 'us-west-2',
  credentials: {
    accessKeyId: import.meta.env.VITE_AWS_ACCESS_KEY_ID || '',
    secretAccessKey: import.meta.env.VITE_AWS_SECRET_ACCESS_KEY || ''
  }
};

export const bedrockConfig = {
  knowledgeBaseId: import.meta.env.VITE_KNOWLEDGE_BASE_ID || '',
}; 