import { fromCognitoIdentityPool } from "@aws-sdk/credential-providers";

export const awsConfig = {
  region: import.meta.env.VITE_AWS_REGION || 'us-west-2',
  credentials: fromCognitoIdentityPool({
    clientConfig: { region: import.meta.env.VITE_AWS_REGION || 'us-west-2' },
    identityPoolId: import.meta.env.VITE_AWS_IDENTITY_POOL_ID || '',
  })
};

export const bedrockConfig = {
  knowledgeBaseId: import.meta.env.VITE_KNOWLEDGE_BASE_ID || '',
}; 