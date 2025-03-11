# Bob - Policy Intelligence Vue Frontend

This is a Vue.js frontend application for the Policy Intelligence system, built with Vue 3 and integrated with AWS Bedrock and Amplify.

## Recommended IDE Setup

[VSCode](https://code.visualstudio.com/) + [Volar](https://marketplace.visualstudio.com/items?itemName=Vue.volar) (and disable Vetur).

## Customize configuration

See [Vite Configuration Reference](https://vite.dev/config/).

## Project Setup

1. Install dependencies:
```sh
npm install
```

2. Configure environment variables:
   - Copy `.env.example` to `.env.local`
   - Fill in the required AWS configuration values

### Development

```sh
npm run dev
```

### Type-Check, Compile and Minify for Production

```sh
npm run build
```

### Run Unit Tests with [Vitest](https://vitest.dev/)

```sh
npm run test:unit
```

### Lint with [ESLint](https://eslint.org/)

```sh
npm run lint
```

## AWS Configuration

This application requires the following AWS services:
- Amazon Bedrock
- Amazon Cognito Identity Pool
- AWS Amplify

Make sure you have the following environment variables set in your `.env.local`:
- `VITE_AWS_REGION`
- `VITE_AWS_IDENTITY_POOL_ID`
- `VITE_KNOWLEDGE_BASE_ID`

## Features

- Document search using Amazon Bedrock
- Chat interface with Claude 3.5 Sonnet
- Document filtering and selection
- Generate responses from selected documents
